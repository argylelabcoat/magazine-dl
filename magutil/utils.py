#!/usr/bin/env python3

import os


def ensuredir(path):
    abpath = os.path.abspath(path)
    if not os.path.exists(abpath):
        os.makedirs(abpath)
