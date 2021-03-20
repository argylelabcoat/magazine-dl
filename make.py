#!/usr/bin/env python3
import configparser
import os
import time

from magutil.http import download_file
from magutil.utils import ensuredir

import requests

from slugify import slugify

# TODO: Deduplicate Download URLs to prevent "same file, different name"


class urls:
    archives="https://www.mydigitalpublication.com/publication/archive.php?id_publication=38377&out=json"


def getArchives(session, magUrl):
    req = session.get(magUrl)
    if req.status_code == 200:
        req = session.get(urls.archives)
        if req.status_code == 200:
            return req.json()['archive']
    return None


def outpath(filename):
    dirname = config['make']['directory']
    filepath = os.path.abspath( os.path.join(dirname, filename) )
    return filepath, os.path.exists(filepath)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('mags.ini')
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    startUrl = config['make']['startUrl']
    archives = getArchives(session, startUrl)

    ensuredir(config['make']['directory'])
    if archives:
        for zine in archives['issue']:
            attrs = zine['@attributes']
            if 'pdf' in attrs:
                date = attrs['date']
                name = attrs['issue_name']
                desc = attrs['description']
                dlurl = attrs['pdf']
                filename = slugify(f'{name}-{desc}')+".pdf"
                print(filename, dlurl)
                filepath, exists = outpath(filename)
                if not exists:
                    download_file(session, dlurl, startUrl, filepath)
                    time.sleep(5)
