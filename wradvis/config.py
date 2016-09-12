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
import os


# Initialise default configuration object
def init_conf():

    conf = ConfigParser()

    conf["dirs"] = {"data": os.path.join(os.getcwd(), "data/rw/20160529") }
    conf["source"] = {"product": "RW", "loc": ""}
    conf["vis"] = {"cmax": 50, "cmin": 0}

    return(conf)

conf = init_conf()