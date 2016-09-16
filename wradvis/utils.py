# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python

"""
"""

import wradlib as wrl
import numpy as np
import netCDF4 as nc
import datetime as dt
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

def dx_to_wgs84(coords):

    # currently works only with radar feldberg
    #Todo: make this work with all DWD-radars and also with other radars
    radar = {'name': 'Feldberg', 'wmo': 10908, 'lon': 8.00361,
             'lat': 47.87361,
             'alt': 1516.10}

    sitecoords = (radar["lon"], radar["lat"],
                  radar["alt"])

    proj_radar = wrl.georef.create_osr("aeqd", lat_0=radar["lat"],
                                       lon_0=radar["lon"])

    radius = wrl.georef.get_earth_radius(radar["lat"], proj_radar)

    lon, lat, height = wrl.georef.polar2lonlatalt_n(coords[1] * 1000,
                                                    coords[0],
                                                    0.8,
                                                    sitecoords,
                                                    re=radius,
                                                    ke=4. / 3.)

    return np.hstack((lon, lat))


def get_radolan_grid():
    return wrl.georef.get_radolan_grid()


def get_radolan_origin():
    return wrl.georef.get_radolan_grid()[0, 0]


def read_radolan(f, missing=-9999, loaddata=True):
    return read_RADOLAN_composite(f, missing=missing, loaddata=loaddata)


def read_dx(f, missing=0, loaddata=True):
    return wrl.io.readDX(f)


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

# just for testing purposes, this can be used from wradlib when it is finalized
# and adapted
def read_RADOLAN_composite(fname, missing=-9999, loaddata=True):
    """Read quantitative radar composite format of the German Weather Service

    The quantitative composite format of the DWD (German Weather Service) was
    established in the course of the `RADOLAN project <http://www.dwd.de/RADOLAN>`
    and includes several file types, e.g. RX, RO, RK, RZ, RP, RT, RC, RI, RG, PC,
    PG and many, many more.
    (see format description on the RADOLAN project homepage :cite:`DWD2009`).

    At the moment, the national RADOLAN composite is a 900 x 900 grid with 1 km
    resolution and in polar-stereographic projection. There are other grid resolutions
    for different composites (eg. PC, PG)

    **Beware**: This function already evaluates and applies the so-called PR factor which is
    specified in the header section of the RADOLAN files. The raw values in an RY file
    are in the unit 0.01 mm/5min, while read_RADOLAN_composite returns values
    in mm/5min (i. e. factor 100 higher). The factor is also returned as part of
    attrs dictionary under keyword "precision".

    Parameters
    ----------
    fname : path to the composite file

    missing : value assigned to no-data cells

    Returns
    -------
    output : tuple of two items (data, attrs)
        - data : numpy array of shape (number of rows, number of columns)
        - attrs : dictionary of metadata information from the file header

    """

    NODATA = missing
    mask = 0xFFF  # max value integer

    f = wrl.io.get_radolan_filehandle(fname)

    header = wrl.io.read_radolan_header(f)

    attrs = wrl.io.parse_DWD_quant_composite_header(header)

    if not loaddata:
        f.close()
        return None, attrs

    attrs["nodataflag"] = NODATA

    #if not attrs["radarid"] == "10000":
    #    warnings.warn("WARNING: You are using function e" +
    #                  "wradlib.io.read_RADOLAN_composit for a non " +
    #                  "composite file.\n " +
    #                  "This might work...but please check the validity " +
    #                  "of the results")

    # read the actual data
    indat = wrl.io.read_radolan_binary_array(f, attrs['datasize'])

    # data handling taking different product types into account
    # RX, EX, WX 'qualitative', temporal resolution 5min, RVP6-units [dBZ]
    if attrs["producttype"] in ["RX", "EX", "WX"]:
        #convert to 8bit unsigned integer
        arr = np.frombuffer(indat, np.uint8).astype(np.uint8)
        # clutter & nodata
        cluttermask = np.where(arr == 249)[0]
        nodatamask = np.where(arr == 250)[0]
        #attrs['cluttermask'] = np.where(arr == 249)[0]

        #arr = np.where(arr >= 249, np.int32(255), arr)

    elif attrs['producttype'] in ["PG", "PC"]:
        arr = wrl.io.decode_radolan_runlength_array(indat, attrs)
    else:
        # convert to 16-bit integers
        arr = np.frombuffer(indat, np.uint16).astype(np.uint16)
        # evaluate bits 13, 14, 15 and 16
        secondary = np.where(arr & 0x1000)[0]
        attrs['secondary'] = np.where(arr & 0x1000)[0]
        #attrs['nodata'] = np.where(arr & 0x2000)[0]
        nodatamask = np.where(arr & 0x2000)[0]
        negative = np.where(arr & 0x4000)[0]
        cluttermask = np.where(arr & 0x8000)[0]
        #attrs['cluttermask'] = np.where(arr & 0x8000)[0]

        # mask out the last 4 bits
        arr = arr & mask

        # consider negative flag if product is RD (differences from adjustment)
        if attrs["producttype"] == "RD":
            # NOT TESTED, YET
            arr[negative] = -arr[negative]
        # apply precision factor
        # this promotes arr to float if precision is float
        #arr = arr * attrs["precision"]
        # set nodata value#
        #arr[attrs['secondary']] = np.int32(4096)
        #arr[nodata] = np.int32(4096)#NODATA

    if nodatamask is not None:
        attrs['nodatamask'] = nodatamask
    if cluttermask is not None:
        attrs['cluttermask'] = cluttermask
    #arr[np.where(arr == 2500)[0]] = np.int32(4096)
    #arr[np.where(arr == 2490)[0]] = np.int32(4096)
    #arr[nodata] = np.int32(0)
    #arr[clutter] = np.int32(65535)
    # anyway, bring it into right shape
    arr = arr.reshape((attrs["nrow"], attrs["ncol"]))
    #arr = arr.reshape((attrs["nrow"], attrs["ncol"]))

    return arr, attrs


def open_ncdf(filename):
    return nc.Dataset(filename, 'r', format='NETCDF4')


def create_ncdf(filename, attrs, units='original'):

    nx = attrs['ncol']
    ny = attrs['nrow']
    version = attrs['radolanversion']
    precision = attrs['precision']
    prodtype = attrs['producttype']
    int = attrs['intervalseconds']
    nodata = attrs['nodataflag']
    missing_value = None

    # create NETCDF4 file in memory
    id = nc.Dataset(filename, 'w', format='NETCDF4', diskless=True, persist=True)
    #id.close()
    #id = nc.Dataset(filename, 'a', format='NETCDF4')

    # create dimensions
    yid = id.createDimension('y', ny)
    xid = id.createDimension('x', nx)
    tbid = id.createDimension('nv', 2)
    tid = id.createDimension('time', None)

    # create and set the grid x variable that serves as x coordinate
    xiid = id.createVariable('x', 'f4', ('x'))
    xiid.axis = 'X'
    xiid.units = 'km'
    xiid.long_name = 'x coordinate of projection'
    xiid.standard_name = 'projection_x_coordinate'

    # create and set the grid y variable that serves as y coordinate
    yiid = id.createVariable('y', 'f4', ('y'))
    yiid.axis = 'Y'
    yiid.units = 'km'
    yiid.long_name = 'y coordinate of projection'
    yiid.standard_name = 'projection_y_coordinate'

    # create time variable
    tiid = id.createVariable('time', 'f8', ('time',))
    tiid.axis = 'T'
    tiid.units = 'seconds since 1970-01-01 00:00:00'
    tiid.standard_name = 'time'
    tiid.bounds = 'time_bnds'

    # create time bounds variable
    tbiid = id.createVariable('time_bnds', 'f8', ('time', 'nv',))

    # create grid variable that serves as lon coordinate
    lonid = id.createVariable('lon', 'f4', ('y', 'x',), zlib=True, complevel=4)
    lonid.units = 'degrees_east'
    lonid.standard_name = 'longitude'
    lonid.long_name = 'longitude coordinate'

    # create grid variable that serves as lat coordinate
    latid = id.createVariable('lat', 'f4', ('y', 'x',), zlib=True, complevel=4)
    latid.units = 'degrees_north'
    latid.standard_name = 'latitude'
    latid.long_name = 'latitude coordinate'

    # create projection variable that defines the projection according to CF-Metadata standards
    coordid = id.createVariable('polar_stereographic', 'i4', zlib=True,
                                complevel=2)
    coordid.grid_mapping_name = 'polar_stereographic'
    coordid.straight_vertical_longitude_from_pole = np.float32(10.)
    coordid.latitude_of_projection_origin = np.float32(90.)
    coordid.standard_parallel = np.float32(60.)
    coordid.false_easting = np.float32(0.)
    coordid.false_northing = np.float32(0.)
    coordid.earth_model_of_projection = 'spherical'
    coordid.earth_radius_of_projection = np.float32(6370.04)
    coordid.units = 'km'
    coordid.ancillary_data = 'grid_latitude grid_longitude'
    coordid.long_name = 'polar_stereographic'

    if prodtype in ['RX', 'EX']:
        if units == 'original':
            scale_factor = None
            add_offset = None
            unit = 'RVP6'
        else:
            scale_factor = np.float32(0.5)
            add_offset = np.float32(-32.5)
            unit = 'dBZ'

        valid_min = np.int32(0)
        valid_max = np.int32(255)
        missing_value = np.int32(255)
        fillvalue = np.int32(255)
        vtype = 'u1'
        standard_name = 'equivalent_reflectivity_factor'
        long_name = 'equivalent_reflectivity_factor'

    elif prodtype in ['RY', 'RZ', 'EY', 'EZ']:
        if units == 'original':
            scale_factor = None
            add_offset = None
            unit = '0.01mm 5min-1'
        elif units == 'normal':
            scale_factor = np.float32(precision * 3600 / int)
            add_offset = np.float(0)
            unit = 'mm h-1'
        else:
            scale_factor = np.float32(precision / (int * 1000))
            add_offset = np.float(0)
            unit = 'm s-1'

        valid_min = np.int32(0)
        valid_max = np.int32(4095)
        missing_value = np.int32(4096)
        fillvalue = np.int32(65535)
        vtype = 'u2'
        standard_name = 'rainfall_amount'
        long_name = 'rainfall_amount'

    elif prodtype in ['RH', 'RB', 'RW', 'RL', 'RU', 'EH', 'EB', 'EW']:
        if units == 'original':
            scale_factor = None
            add_offset = None
            unit = '0.1mm h-1'
        elif units == 'normal':
            scale_factor = np.float32(precision)
            add_offset = np.float(0.)
            unit = 'mm h-1'
        else:
            scale_factor = np.float32(precision / (int * 1000))
            add_offset = np.float(0)
            unit = 'm s-1'

        valid_min = np.int32(0)
        valid_max = np.int32(4095)
        missing_value = np.int32(4096)
        fillvalue = np.int32(65535)
        vtype = 'u2'
        standard_name = 'rainfall_amount'
        long_name = 'rainfall_amount'

    elif prodtype in ['SQ', 'SH', 'SF']:
        scale_factor = np.float32(precision)
        add_offset = np.float(0.)
        valid_min = np.int32(0)
        valid_max = np.int32(4095)
        missing_value = np.int32(4096)
        fillvalue = np.int32(65535)
        vtype = 'u2'
        standard_name = 'rainfall_amount'
        long_name = 'rainfall_amount'
        if int == (360 * 60):
            unit = 'mm 6h-1'
        elif int == (720 * 60):
            unit = 'mm 12h-1'
        elif int == (1440 * 60):
            unit = 'mm d-1'

    prod = id.createVariable('data', vtype, ('time', 'y', 'x',),
                             fill_value=fillvalue, zlib=True, complevel=4,
                             chunksizes=(1, 32, 32))
    # accept data as unsigned byte without scaling, crucial for writing already packed data
    #prod.set_auto_maskandscale(False)
    prod.units = unit
    prod.standard_name = standard_name
    prod.long_name = long_name
    prod.grid_mapping = 'polar_stereographic'
    prod.coordinates = 'lat lon'
    if scale_factor:
        prod.scale_factor = scale_factor
    if add_offset:
        prod.add_offset = add_offset
    if valid_min:
        prod.valid_min = valid_min
    if valid_max:
        prod.valid_max = valid_max
    if missing_value:
        prod.missing_value = missing_value
    prod.version = 'RADOLAN {0}'.format(version)
    prod.source = prodtype
    prod.comment = 'NO COMMENT'

    id_str1 = id.createVariable('radars', 'S128', ('time',), zlib=True,
                                complevel=4)

    # create GLOBAL attributes
    id.Title = 'RADOLAN {0} Composite'.format(prodtype)
    id.Institution = 'Data owned by Deutscher Wetterdienst'
    id.Source = 'DWD C-Band Weather Radar Network, Original RADOLAN Data by Deutscher Wetterdienst'
    id.History = 'Data transferred from RADOLAN composite format to netcdf using wradvis version 0.1 by wradlib developers'
    id.Conventions = 'CF-1.6 where applicable'
    utcnow = dt.datetime.utcnow()
    id.Processing_date = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
    id.Author = '{0}, {1}'.format('Author', 'wradlib@wradlib.org')
    id.Comments = 'blank'
    id.License = 'DWD Licenses'



    # fill general variables
    ny, nx = attrs['ncol'], attrs['nrow']
    radolan_grid_xy = wrl.georef.get_radolan_grid(nx, ny)
    xarr = radolan_grid_xy[0, :, 0]
    yarr = radolan_grid_xy[:, 0, 1]
    radolan_grid_ll = wrl.georef.get_radolan_grid(nx, ny, wgs84=True)
    lons = radolan_grid_ll[..., 0]
    lats = radolan_grid_ll[..., 1]


    id.variables['x'][:] = xarr
    id.variables['x'].valid_min = xarr[0]
    id.variables['x'].valid_max = xarr[-1]
    id.variables['y'][:] = yarr
    id.variables['y'].valid_min = yarr[0]
    id.variables['y'].valid_max = yarr[-1]
    id.variables['lat'][:] = lats
    id.variables['lon'][:] = lons

    return id


def add_ncdf(id, data, time_index, attrs):
    # remove clutter, nodata and secondary data from raw files
    # wrap with if/else if necessary
    if attrs['cluttermask'] is not None:
        data.flat[attrs['cluttermask']] = id.variables[
            'data'].missing_value
    if attrs['nodatamask'] is not None:
        data.flat[attrs['nodatamask']] = id.variables[
            'data'].missing_value
    #if attrs['secondary'] is not None:
    #    data.flat[attrs['secondary']] = id.variables[
    #        attrs['producttype'].lower()].missing_value

    id.variables['data'].set_auto_maskandscale(False)
    id.variables['data'][time_index, :, :] = data
    id.variables['data'].set_auto_maskandscale(True)
    print(attrs['datetime'])
    delta = attrs['datetime'] - dt.datetime.utcfromtimestamp(0)
    id.variables['time'][time_index] = delta.total_seconds()
    id.variables['time_bnds'][time_index, :] = delta.total_seconds()
    # id.variables['time_bnds'][time_index,1] = delta.total_seconds() + attrs['intervalseconds']
    id.variables['radars'][time_index] = ','.join(attrs['radarlocations'])


def get_dt(unix):
    return dt.datetime.utcfromtimestamp(unix)
