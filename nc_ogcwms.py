def nc_georeference(dir_path, save_dir_path, compress):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime
    THREDDS Documentation specifies that an appropriately georeferenced file should
    1. Has Coordinate Variables- 2 1D variables, lat lon, which contain the lat/lon values of the grid points.
        Each variable requires only 1 Dimension.
    2. Has 2 dimensions, lat lon, that are the Coordinate Dimensions corresponding to the Coordinate Variables.
    3. Each variable requires the Coordinate Dimensions.
    3. Has global attributes called _Coordinate**
    """
    import netCDF4
    import os
    import datetime

    files = os.listdir(dir_path)
    files = [file for file in files if file.startswith('LIS_HIST_')]
    print('There are ' + str(len(files)) + ' compatible files. They are:')
    print(files)

    # read the first file in the list to get some data
    print('Preparing the reference file')
    path = os.path.join(dir_path, files[0])
    netcdf_obj = netCDF4.Dataset(path, 'r', clobber=False, diskless=True)

    # get a dictionary of the dimensions and their size and rename the north/south and east/west ones
    dimensions = {}
    for dimension in netcdf_obj.dimensions.keys():
        dimensions[dimension] = netcdf_obj.dimensions[dimension].size
    dimensions['lat'] = dimensions['north_south']
    dimensions['lon'] = dimensions['east_west']
    del dimensions['north_south'], dimensions['east_west']  # , dimensions['ensemble']
    dimensions['time'] = 7

    # get a list of the variables and remove the one's i'm going to 'manually' correct
    variables = netcdf_obj.variables
    del variables['lat'], variables['lon']  # , variables['ensemble']
    variables = variables.keys()

    # min lat and lon and the interval between values
    lat_min = netcdf_obj.__dict__['SOUTH_WEST_CORNER_LAT']
    lon_min = netcdf_obj.__dict__['SOUTH_WEST_CORNER_LON']
    lat_step = netcdf_obj.__dict__['DX']
    lon_step = netcdf_obj.__dict__['DY']

    netcdf_obj.close()

    # this is where the files start getting copied
    for file in files:
        print('Working on file ' + str(file))
        openpath = os.path.join(dir_path, file)
        savepath = os.path.join(save_dir_path, 'processed_' + file)
        # open the file to be copied
        original = netCDF4.Dataset(openpath, 'r', clobber=False, diskless=True)
        duplicate = netCDF4.Dataset(savepath, 'w', clobber=True, format='NETCDF4', diskless=False)
        # set the global netcdf attributes - important for georeferencing
        duplicate.setncatts(original.__dict__)

        # specify dimensions from what we copied before
        for dimension in dimensions:
            duplicate.createDimension(dimension, dimensions[dimension])

        for dim in duplicate.dimensions.keys():
            print(dim)
            print(duplicate.dimensions[dim])

        # 'Manually' create the dimensions that need to be set carefully
        if compress:
            duplicate.createVariable(varname='lat', datatype='f4', dimensions='lat', zlib=True, shuffle=True)
            duplicate.createVariable(varname='lon', datatype='f4', dimensions='lon', zlib=True, shuffle=True)
        else:
            duplicate.createVariable(varname='lat', datatype='f4', dimensions='lat')
            duplicate.createVariable(varname='lon', datatype='f4', dimensions='lon')

        # create the lat and lon values as a 1D array
        lat_list = [lat_min + i * lat_step for i in range(dimensions['lat'])]
        lon_list = [lon_min + i * lon_step for i in range(dimensions['lon'])]
        duplicate['lat'][:] = lat_list
        duplicate['lon'][:] = lon_list

        # set the attributes for lat and lon individually
        for attr in original['lat'].__dict__:
            if attr != "_FillValue":
                duplicate['lat'].setncattr(attr, original['lat'].__dict__[attr])

        for attr in original['lon'].__dict__:
            if attr != "_FillValue":
                duplicate['lon'].setncattr(attr, original['lon'].__dict__[attr])

        # copy the rest of the variables
        for variable in variables:
            print('Copying variable ' + variable)
            # check to use the lat/lon dimension names
            dimension = original[variable].dimensions
            if 'north_south' in dimension:
                dimension = list(dimension)
                dimension.remove('north_south')
                dimension.append('lat')
                dimension = tuple(dimension)
            if 'east_west' in dimension:
                dimension = list(dimension)
                dimension.remove('east_west')
                dimension.append('lon')
                dimension = tuple(dimension)
            # if 'ensemble' in dimension:
            #     dimension = list(dimension)
            #     dimension.append('time')
            #     dimension.remove('ensemble')
            #     dimension = tuple(dimension)

            # create the variable
            if compress:
                duplicate.createVariable(varname=variable, datatype='f4', dimensions=dimension, zlib=True, shuffle=True)
            else:
                duplicate.createVariable(varname=variable, datatype='f4', dimensions=dimension)
            # copy the attributes
            for attr in original[variable].__dict__:
                if attr != "_FillValue":
                    duplicate[variable].setncattr(attr, original[variable].__dict__[attr])
            # copy the arrays of data
            if variable == 'time':
                duplicate[variable][:] = [1, 2, 3, 4, 5, 6, 7]
            else:
                duplicate[variable][:] = original[variable][:]

        # close the files and start again
        original.close()
        duplicate.sync()
        duplicate.close()

    return


nc_georeference(r'/Users/rileyhales/thredds/forecasts/', r'/Users/rileyhales/thredds/sampleoutputs/', compress=True)
