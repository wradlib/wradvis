# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python

"""
"""

# Python 2/3 compatibility: for Python 2, you need to install configparser
# see requirements.txt
from configparser import ConfigParser

# Initialise default configuration object

def init_conf():

    conf = ConfigParser()

    conf['DEFAULT'] = {'ServerAliveInterval': '45',
                         'Compression': 'yes',
                         'CompressionLevel': '9'}
    conf['bitbucket.org'] = {}
    conf['bitbucket.org']['User'] = 'hg'
    conf['topsecret.server.com'] = {}
    topsecret = conf['topsecret.server.com']
    topsecret['Port'] = '50022'     # mutates the parser
    topsecret['ForwardX11'] = 'no'  # same here
    conf['DEFAULT']['ForwardX11'] = 'yes'
    with open('example.ini', 'w') as configfile:
        conf.write(configfile)