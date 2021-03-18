#!/usr/bin/env python3
import os
import re
import time
import configparser

from bs4 import BeautifulSoup

import requests


## TODO: Relocate DownloadFile to a common "library"
## TODO: Deduplicate Download URLs to prevent "same file, different name"


class urls:
    archives="https://www.mydigitalpublication.com/publication/archive.php?id_publication=38377&out=json"


def outpath(filename):
    dirname = config['make']['directory']
    filepath = os.path.abspath( os.path.join(dirname, filename) )
    return filepath, os.path.exists(filepath)


def getArchives(session, magUrl):
    req = session.get(magUrl)
    if req.status_code == 200:
        req = session.get(urls.archives)
        if req.status_code == 200:
            return req.json()
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

    startUrl = config['make']['startUrl']
    archives = getArchives(session, startUrl)
    if archives:
        print(archives)
        for zine in archives:
            issue, magurl = zine
            dlurl = getMagDLUrl(session, magurl)
            print(issue, magurl, dlurl)
