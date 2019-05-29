import netCDF4, os, datetime


def nc_georeference(dir_path, save_dir_path, compress):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime (you'll need to add this)
    THREDDS Documentation specifies that an appropriately georeferenced file should
    1. 2 Coordinate Dimensions, lat and lon. Their size is the number of steps across the grid.
    2. 2 Coordinate Variables, lat and lon, whose arrays contain the lat/lon values of the grid points.
        These variables only require the corresponding lat or lon dimension.
    3. 1 time dimension whose length is the number of time steps
    4. 1 time variable whose array contains the difference in time between steps using the units given in the metadata.
    5. Each variable requires the the time and Coordinate Dimensions, in that order (time, lat, lon)
    6. Each variable has the long_name, units, standard_name property values correct
    7. The variable property coordinates = "lat lon" or else is blank/doesn't exist
    """
    # list the files that need to be converted
    files = os.listdir(dir_path)
    files = [file for file in files if file.endswith('.nc') and not file.startswith('gfs')]

    # read the first file that we'll copy data from in the next blocks of code
    path = os.path.join(dir_path, files[0])
    netcdf_obj = netCDF4.Dataset(path, 'r', clobber=False, diskless=True)

    # get a dictionary of the dimensions and their size and rename the north/south and east/west ones
    dimensions = {}
    for dimension in netcdf_obj.dimensions.keys():
        dimensions[dimension] = netcdf_obj.dimensions[dimension].size
    dimensions['lat'] = dimensions['latitude']
    dimensions['lon'] = dimensions['longitude']
    dimensions['time'] = 1
    del dimensions['latitude'], dimensions['longitude']

    # get a list of the variables and remove the one's i'm going to 'manually' correct
    variables = netcdf_obj.variables
    del variables['valid_time'], variables['step'], variables['latitude'], variables['longitude'], variables['surface']
    variables = variables.keys()

    # min lat and lon and the interval between values (these are static values
    lat_min = -90
    lon_min = -180
    lat_step = .25
    lon_step = .25
    # lat_min = netcdf_obj.__dict__['SOUTH_WEST_CORNER_LAT']
    # lon_min = netcdf_obj.__dict__['SOUTH_WEST_CORNER_LON']
    # lat_step = netcdf_obj.__dict__['DX']
    # lon_step = netcdf_obj.__dict__['DY']

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

        # set the attributes for lat and lon (except fill value, you just can't copy it)
        for attr in original['latitude'].__dict__:
            if attr != "_FillValue":
                duplicate['lat'].setncattr(attr, original['latitude'].__dict__[attr])
        for attr in original['longitude'].__dict__:
            if attr != "_FillValue":
                duplicate['lon'].setncattr(attr, original['longitude'].__dict__[attr])

        # copy the rest of the variables
        date = 'this is where you have controls for setting the dates'
        timestep = 1
        timedelta = 'add an expression for changing back and forth'
        for variable in variables:
            # check to use the lat/lon dimension names
            dimension = original[variable].dimensions
            if 'latitude' in dimension:
                dimension = list(dimension)
                dimension.remove('latitude')
                dimension.append('lat')
                dimension = tuple(dimension)
            if 'longitude' in dimension:
                dimension = list(dimension)
                dimension.remove('longitude')
                dimension.append('lon')
                dimension = tuple(dimension)
            if len(dimension) == 2:
                dimension = ('time', 'lat', 'lon')
            if variable == 'time':
                dimension = ('time',)

            # create the variable
            if compress:
                duplicate.createVariable(varname=variable, datatype='f4', dimensions=dimension, zlib=True, shuffle=True)
            else:
                duplicate.createVariable(varname=variable, datatype='f4', dimensions=dimension)

            # copy the arrays of data and set the metadata/properties
            if variable == 'time':
                duplicate[variable][:] = [timestep]
                timestep += timedelta
                duplicate[variable].long_name = original[variable].long_name
                duplicate[variable].units = "hours since " + date
                duplicate[variable].axis = "T"  # or time
                # also set the begin date of this data
                duplicate[variable].begin_date = date
            if variable == 'lat':
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "Y"  # or lat
            if variable == 'lon':
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "X"  # or lon
            else:
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "lat lon"
            duplicate[variable].long_name = original[variable].long_name
            duplicate[variable].begin_date = date
            duplicate[variable].units = original[variable].unit

        # close the files, delete the one you just did, start again
        original.close()
        duplicate.sync()
        duplicate.close()
        os.remove(openpath)

    return


nc_georeference(r'/Users/rileyhales/thredds/forecasts/', r'/Users/rileyhales/thredds/sampleoutputs/', compress=True)
