import netCDF4, os


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
        if dimension == 'latitude' or dimension == 'north_south':
            dimensions['lat'] = dimensions[dimension]
            del dimensions[dimension]
        elif dimension == 'longitude' or dimension == 'east_west':
            dimensions['lon'] = dimensions[dimension]
            del dimensions[dimension]
    dimensions['time'] = 1

    # get a list of the variables and remove the one's i'm going to 'manually' correct
    variables = netcdf_obj.variables
    for variable in ['valid_time', 'step', 'latitude', 'longitude', 'surface', 'lat', 'lon']:
        try:
            del variables[variable]
        except AttributeError:
            pass
    variables = variables.keys()

    # min lat and lon and the interval between values (these are static values)
    lat_min = 8
    lon_min = 58
    lat_step = .05
    lon_step = .05

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
        for attr in original['lat'].__dict__:
            if attr != "_FillValue":
                duplicate['lat'].setncattr(attr, original['lat'].__dict__[attr])
        for attr in original['lon'].__dict__:
            if attr != "_FillValue":
                duplicate['lon'].setncattr(attr, original['lon'].__dict__[attr])

        # copy the rest of the variables
        date = '201906'
        timestep = 0
        timedelta = 1
        for variable in variables:
            # check to use the lat/lon dimension names
            dimension = original[variable].dimensions
            if 'latitude' in dimension:
                dimension = list(dimension)
                dimension.remove('latitude')
                dimension.append('lat')
                dimension = tuple(dimension)
            if 'north_south' in dimension:
                dimension = list(dimension)
                dimension.remove('north_south')
                dimension.append('lat')
                dimension = tuple(dimension)
            if 'longitude' in dimension:
                dimension = list(dimension)
                dimension.remove('longitude')
                dimension.append('lon')
                dimension = tuple(dimension)
            if 'east_west' in dimension:
                dimension = list(dimension)
                dimension.remove('east_west')
                dimension.append('lon')
                dimension = tuple(dimension)
            if 'time' not in dimension:
                dimension = list(dimension)
                dimension = ['time'] + dimension
                dimension = tuple(dimension)
            if len(dimension) == 2:
                dimension = ('time', 'lat', 'lon')
            if variable == 'time':
                dimension = ('time',)

            print(variable)
            print(dimension)

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

            duplicate[variable].begin_date = date
            try:
                duplicate[variable].long_name = original[variable].long_name
            except AttributeError:
                duplicate[variable].long_name = variable
            try:
                duplicate[variable].units = original[variable].units
            except AttributeError:
                duplicate[variable].units = 'unknown units'

        # close the file then start again
        original.close()
        duplicate.sync()
        duplicate.close()

    return


nc_georeference(r'/path/to/data/', r'/path/to/save', compress=True)
