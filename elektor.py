#!/usr/bin/env python3
import configparser
import os
import re
import time

from bs4 import BeautifulSoup

from magutil.http import download_file
from magutil.utils import ensuredir

import requests


# TODO: Deduplicate Download URLs to prevent "same file, different name"

class urls:
    login = 'https://www.elektormagazine.com/account/login'
    mags = 'https://www.elektormagazine.com/magazine/{year}'


def outpath(filename):
    dirname = config['elektor']['directory']
    filepath = os.path.abspath( os.path.join(dirname, filename) )
    return filepath, os.path.exists(filepath)


def login(session, email, password, token):
    payload = {
        'email': email,
        'password': password,
        'remember': "1",
        '_token': token,
        'intended': ""}

    req = session.post(urls.login, data=payload)
    return req.status_code == 200


def getToken(session):
    req = session.get(urls.login)
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, features='html.parser')
        loginform = soup.find("form", attrs={'action': urls.login})
        if loginform:
            token_input = loginform.find("input", attrs={'name': '_token'})
            if token_input:
                return token_input['value']

    return None


def getMagDLUrl(session, magUrl):
    req = session.get(magUrl)
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, features='html.parser')
        dlbutton = soup.find("div", class_="download")
        if dlbutton:
            anchor = dlbutton.find("a")
            if anchor:
                return anchor['href']
    return None


def getMagList(session, year):
    issueRe = re.compile('\d{4,4}-\d{1,2}')
    magUrl = urls.mags.format(year=year)
    req = session.get(magUrl)
    magurls = []
    urlset = set()
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, features='html.parser')
        maglinks = soup.find_all("p", class_="Magazine__month")
        if maglinks and len(maglinks) > 0:
            for linkp in maglinks:
                anchor=linkp.find('a')
                issueM = issueRe.search(anchor.text)
                if issueM :
                    issue=f'elektor-{issueM.group(0)}.pdf'
                    issuePath, exists = outpath(issue)
                    if not exists:
                        dlUrl = getMagDLUrl(session, anchor['href'])
                        if dlUrl and dlUrl not in urlset:
                            urlset.add(dlUrl)
                            magurls.append((issuePath, dlUrl, magUrl))
    else:
        return None

    if len(magurls) > 0:
        return magurls
    return None


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('mags.ini')
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    password = config['elektor']['password']
    email = config['elektor']['email']
    startYear = int(config['elektor']['startYear'])
    endYear   = int(config['elektor']['endYear']) + 1
    ensuredir(config['elektor']['directory'])
    print("from", startYear, "to", endYear)
    token = getToken(session)
    loggedIn = False
    if token:
        print("Logging in...")
        loggedIn = login(session, email, password, token)
        if loggedIn:
            print("Logged in.")
            for year in range(startYear, endYear):
                print("gettings year:", year)
                magsForYear = getMagList(session, year)
                if magsForYear and len(magsForYear) > 0:
                    for mag in magsForYear:
                        issue, url, refer = mag
                        if not os.path.exists(issue):
                            saved = download_file(session, url, refer, issue)
                            time.sleep(5)
