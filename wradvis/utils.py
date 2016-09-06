# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python

"""
"""

import wradlib as wrl
from wradvis.config import conf


def wgs84_to_radolan(coords):

    proj_wgs = wrl.georef.epsg_to_osr(4326)
    proj_stereo = wrl.georef.create_osr("dwd-radolan")
    xy = wrl.georef.reproject(coords,
                              projection_source=proj_wgs,
                              projection_target=proj_stereo)
    return xy


def radolan_to_wgs84(coords):

    proj_wgs = wrl.georef.epsg_to_osr(4326)
    proj_stereo = wrl.georef.create_osr("dwd-radolan")
    ll = wrl.georef.reproject(coords,
                              projection_source=proj_stereo,
                              projection_target=proj_wgs)
    return ll


def get_radolan_origin():
    return wrl.georef.get_radolan_grid()[0, 0]


def read_radolan(f, missing=0, loaddata=True):
    return wrl.io.read_RADOLAN_composite(f, missing=missing, loaddata=loaddata)


def get_cities_coords():

    cities = {}
    cities[u'Köln'] = (6.95, 50.95)   # lat, lon; Unicode fr Umlaute
    cities[u"Hamburg"] = (10.0, 53.55)
    cities[u"Frankfurt"] = (8.7,50.1)
    cities[u"Eisenach"] = (10.3, 51.0)
    cities[u"Dresden"]=(13.7,51.1)
    cities[u"Freiburg"]=(7.9,48.0)
    cities[u"Berlin"]=(13.4,52.5)
    cities[u"München"]=(11.58,48.14)

    return cities


