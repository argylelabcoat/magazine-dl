#!/usr/bin/env python3
import os
import time


def download_file(session, url, refer, filename):
    success = False
    tries = 0
    while success == False and tries < 10:
        try:
            with session.get(url, headers={'referer': refer}, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            print("Error: ", e)
            if os.path.exists(filename):
                os.remove(filename)
            tries += 1
            time.sleep(5)
        finally:
            success = True

    return filename
