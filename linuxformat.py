#!/usr/bin/env python3
import configparser
import os
import re
import time

from bs4 import BeautifulSoup

from magutil.http import download_file

import requests


# TODO: Deduplicate Download URLs to prevent "same file, different name"

class urls:
    login = 'https://www.linuxformat.com/subsarea'
    mags  = 'https://www.linuxformat.com/archives'
    issue = 'https://www.linuxformat.com/archives?issue={issue}'



def outpath(filename):
    dirname = config['linuxformat']['directory']
    filepath = os.path.abspath( os.path.join(dirname, filename) )
    return filepath, os.path.exists(filepath)


def login(session, number, surname):
    payload = {
        'Number': number,
        'Surname': surname,
        }

    req = session.post(urls.login, data=payload)
    return req.status_code == 200


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


def getMagList(session):
    req = session.get(urls.mags)
    magurls = []
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, features='html.parser')
        issueList = soup.find("select", attrs={'name': 'issue'})
        issueOptions = issueList.find_all('option')
        for option in issueOptions:
            issueUrl = urls.issue.format(issue=option.text)
            magurls.append((issueUrl, int(option.text)))
        return magurls
    return None


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('mags.ini')
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    sub_number = config['linuxformat']['subscriptionNo']
    surname = config['linuxformat']['surname']
    startIssue = int(config['linuxformat']['startIssue'])
    loggedIn = login(session, sub_number, surname)
    if loggedIn:
        mags = getMagList(session)
        for issue in mags:
            issueUrl, issueNo = issue
            if issueNo >= startIssue:
                print(issueUrl, issueNo)
        exit()
