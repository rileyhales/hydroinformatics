import netCDF4, os

src_path = r'C:/Users/username/Documents/netcdf_directory/'
dst_path = r'C:/Users/username/Documents/'
var = 'var_name'
params = [.25, 1440, -179.875, 179.875, 600, -59.875, 89.875]

# This function can be used to preprocess datasets
def timeseries_netcdfDir(src_path, dst_path, var, params):
    """
    Dependencies: netCDF4, os
    Author: Riley Hales
    Revised Date: October 4 2018
    Description: Merges a directory of netcdfs each with data for 1 day into a properly formatted timeseries netcdf4.
        This function is meant for preprocessing purposes only and should not be called in the app.
    Arguments:
        src_path: string path to the DIRECTORY containing the source files, include the / at the end
        dst_path: string path to the DIRECTORY where the combined timeseries should be saved
        var: string name of the variable you want a timeseries for as recorded in the source files (the shortcode)
        params: a list of parameter settings
            resolution: the increment in degrees between latitude/longitude steps
            lon_size: size of the LONGITUDE dimension in your files. this depends on the resolution
            lon_min: the smallest longitude value
            lon_max: the largest latitude value
            lat_size: size of the LATITUDE dimension in your files. this depends on the resolution
            lat_min: the smallest latitude value
            lat_max: the largest latitude value
                OPTIONAL: for metadata in the dataset
            todo some parameters so you can fill the metadata of the time step
    Results:
        Saves a timeseries in .nc format to the directory specified named the same as the variable it displays
    Known Bugs:
        The program loads timesteps in the alphabetical order it reads the files in. if you data is not in time and
            alphabetical order, your timeseries will be mismatched
        If your input netcdfs use a different order/combination of time, lat, lon dimensions. The program will crash


    """
    # load all the conditions from the parameters
    resolution = params[0]
    lon_size = params[1]
    lon_min = params[2]
    lon_max = params[3]
    lat_size = params[4]
    lat_min = params[5]
    lat_max = params[6]
    print(params)
    print("loaded parameters from list")

    # list all the filed contained in the given source dir
    source_files = os.listdir(src_path)

    # create the new netcdf
    timeseries = netCDF4.Dataset(dst_path + var + '.nc', 'w', clobber=True, format='NETCDF4')

    # specify dimensions
    timeseries.createDimension('lat', lat_size)
    timeseries.createDimension('lon', lon_size)
    timeseries.createDimension('time', len(source_files))

    # create the time variable the way it's supposed to be
    timeseries.createVariable(varname='time', datatype='i4', dimensions='time')
    timeseries['time'].setncattr('units', 'Month since 2000')
    timeseries['time'].setncattr('time_increment', '1 Month')
    # timeseries['time'].setncattr('begin_date', '200001')
    # timeseries['time'].setncattr('begin_time', '000000')
    timeseries['time'].setncattr('name', 'time')
    print("created time dimension and variable")
    timelist = []
    for i in range(len(source_files)):
        timelist.append(i)
    timeseries['time'][:] = timelist
    print("the timesteps are", timelist)

    # create the latitude and longitude variables correctly 'lat' and 'lon'
    timeseries.createVariable(varname='lat', datatype='f4', dimensions='lat')
    timeseries.createVariable(varname='lon', datatype='f4', dimensions='lon')
    print("determining latitude steps")
    lat = lat_min
    lat_list = []
    while lat <= lat_max:
        lat_list.append(lat)
        lat += resolution
    print("there are", len(lat_list), "latitude steps. They are:")
    print(lat_list)
    print("determining longitude steps")
    lon = lon_min
    lon_list = []
    while lon <= lon_max:
        lon_list.append(lon)
        lon += resolution
    print("there are", len(lon_list), "longitude steps. They are:")
    print(lon_list)
    print("storing latitude steps")
    timeseries['lat'][:] = lat_list
    print("storing longitude steps")
    timeseries['lon'][:] = lon_list

    # create the variable the we want to make the time series for
    timeseries.createVariable(varname=var, datatype='f4', dimensions=('lat', 'lon', 'time'))

    # for every file in the folder, open file, assign variable variable data to current time step, next time step
    tstep = 0
    var_list = ['lat', 'lon']
    print("processing the chosen variable information")
    for file in source_files:
        # for each file in the folder, open the file
        source = netCDF4.Dataset(src_path + file)
        print("copying from file " + str(file))
        # set the global attributes, but only once
        if tstep < 1:
            timeseries.setncatts(source.__dict__)
        # copy the variable data to the appropriate places
        for name, variable in source.variables.items():
            # copy the variable specified by the user
            if name == var:
                timeseries[name][:, :, tstep] = source[name][0, :, :]
                tstep += 1
                # set the variable attributes, but only 1 time
                if tstep < 1:
                    for attr in source[name].__dict__:
                        if attr != "_FillValue":
                            timeseries[name].setncattr(attr, source[name].__dict__[attr])
            # copy the other variables, but only the first time because lat/lon is the same for all
            if name in var_list and tstep < 1:
                for attr in source[name].__dict__:
                    if attr != "_FillValue":
                        timeseries[name].setncattr(attr, source[name].__dict__[attr])
        source.close()
        timeseries.sync()
        print("data written to hard drive")
    print("successfully duplicated variable data")

    # sync pushes the data to the disc, close removes the connections to the opened file
    timeseries.sync()
    timeseries.close()

    print("program finished")
    return()

timeseries_netcdfDir(src_path, dst_path, var, params)