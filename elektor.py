#!/usr/bin/env python3
import os
import re
import time
import configparser

from bs4 import BeautifulSoup

import requests


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
                        if dlUrl:
                            magurls.append((issuePath, dlUrl, magUrl))
    else:
        return None

    if len(magurls) > 0:
        return magurls
    return None


def download_file(session, url, refer, filename):
    try:
        with session.get(url, headers={'referer': refer}, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except:
        if os.path.exists(filename):
            os.remove(filename)
        return None

    return filename


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('mags.ini')
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    password = config['elektor']['password']
    email = config['elektor']['email']
    startYear = int(config['elektor']['startYear'])
    endYear   = int(config['elektor']['endYear']) + 1
    print("from", startYear, "to", endYear)
    token = getToken(session)
    loggedIn = False
    if token:
        loggedIn = login(session, email, password, token)
        if loggedIn:
            for year in range(startYear, endYear):
                magsForYear = getMagList(session, year)
                if magsForYear and len(magsForYear) > 0:
                    for mag in magsForYear:
                        issue, url, refer = mag
                        if not os.path.exists(issue):
                            tries = 0
                            print(url, issue)
                            complete = False
                            while complete == False and tries < 10:
                                print("Attempt", tries)
                                saved = download_file(session, url, refer, issue)
                                if saved:
                                    complete = True
                                else:
                                    tries += 1
                                    time.sleep(1)
                            time.sleep(5)
