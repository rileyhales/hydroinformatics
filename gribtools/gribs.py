import os
import shutil
import numpy
import datetime
import netCDF4
import pygrib


def grib_to_netcdf(grib_path, ncpath, **kwargs):
    """
    Turns a grib or directory of gribs containing georeferenced data into netcdfs that are properly formatted
    :param grib_path:
    :param ncpath:
    :param kwargs:
    :return:
    """
    # todo
    # list all the files in the user specified directory
    if os.path.isdir(grib_path):
        files = os.listdir(grib_path)
        files = [i for i in files if i.endswith('.grb') or i.endswith('.grib')]
        files.sort()
    elif os.path.isfile(grib_path):
        split = os.path.split(grib_path)
        grib_path = split[0]
        files = [split[1]]

    # parse the optional argument from the kwargs
    save_dir = kwargs.get('save_dir', grib_path)
    delete_sources = kwargs.get('delete_sources', False)

    # for each grib file you downloaded, open it, convert it to a netcdf
    for level in forecastlevels:
        latitudes = [-90 + (i * .25) for i in range(721)]
        longitudes = [-180 + (i * .25) for i in range(1440)]
        time_dt = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        for file in files:
            # create the new netcdf
            ncname = level + '_' + file.replace('.grb', '.nc')
            ncpath = os.path.join(netcdfs, ncname)
            new_nc = netCDF4.Dataset(ncpath, 'w', clobber=True, format='NETCDF4', diskless=False)

            data_time = time_dt + datetime.timedelta(hours=hour)
            data_time = data_time.strftime("%Y%m%d%H")

            new_nc.createDimension('time', 1)
            new_nc.createDimension('lat', 721)
            new_nc.createDimension('lon', 1440)

            new_nc.createVariable(varname='time', datatype='f4', dimensions='time')
            new_nc['time'].axis = 'T'
            new_nc['time'].begin_date = data_time
            new_nc.createVariable(varname='lat', datatype='f4', dimensions='lat')
            new_nc['lat'].axis = 'lat'
            new_nc.createVariable(varname='lon', datatype='f4', dimensions='lon')
            new_nc['lon'].axis = 'lon'

            # set the value of the time variable data
            new_nc['time'][:] = [hour]

            # read a file to get the lat/lon variable data
            new_nc['lat'][:] = latitudes
            new_nc['lon'][:] = longitudes

            gribpath = os.path.join(grib_path, file)
            gribfile = pygrib.open(gribpath)
            gribfile.seek(0)
            filtered_grib = gribfile(typeOfLevel=level)
            for variable in filtered_grib:
                short = variable.shortName
                if short not in ['time', 'lat', 'lon']:
                    try:
                        new_nc.createVariable(varname=short, datatype='f4', dimensions=('time', 'lat', 'lon'))
                        new_nc[short].units = variable.units
                        new_nc[short].long_name = variable.name
                        new_nc[short].gfs_level = level
                        new_nc[short].begin_date = data_time
                        new_nc[short].axis = 'lat lon'

                        # get array, flip vertical, split and concat to shift from 0-360 degrees to 180-180
                        data = numpy.flip(variable.values, 0)
                        data = numpy.hsplit(data, 2)
                        data = numpy.concatenate((data[1], data[0]), axis=1)
                        new_nc[short][:] = data
                    except:
                        pass
            new_nc.close()
            gribfile.close()

    # delete the gribs now that you're done with them triggering future runs to skip the download step
    shutil.rmtree(grib_path)

    return
