file_path = r'/Users/rileyhales/thredds/malaria/LIS_HIST_20070407.nc'

def variablebounds(file_path):
    """
    Makes a dictionary of variable names with a string 'min,max' of the smallest and largest values
    """
    import netCDF4
    import numpy
    bounds = {}

    data_obj = netCDF4.Dataset(file_path, 'r',
                               clobber=False, diskless=True, persist=False)
    print(data_obj)

    for variable in data_obj.variables.keys():
        min = numpy.min(data_obj[variable][:])
        max = numpy.max(data_obj[variable][:])
        bounds[variable] = str(min) + ',' + str(max)
    print(bounds)
    return bounds
