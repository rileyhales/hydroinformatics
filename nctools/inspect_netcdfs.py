def show_contents(file_path):
    """
    Uses the file at file_path to demonstrate how to access specific data and metadata elements of a netcdf4 dataset
    """
    import netCDF4
    import pprint
    data_obj = netCDF4.Dataset(file_path, 'r', clobber=False, diskless=True, persist=False)

    print("This is your netcdf object")
    pprint.pprint(data_obj)

    print("There are " + str(len(data_obj.variables)) + " variables")       # The number of variables
    print("There are " + str(len(data_obj.dimensions)) + " dimensions")     # The number of dimensions

    print('These are the global attributes of the netcdf file')
    print(data_obj.__dict__)                                    # access the global attributes of the netcdf file
    print(data_obj.__dict__['SOUTH_WEST_CORNER_LAT'])           # access a specific netcdf attribute
    print('')

    print("Detailed view of each variable")
    print('')
    variables = {}
    for variable in data_obj.variables.keys():                  # .keys() gets the name of each variable
        print(variable)                                         # The string name of the variable
        print(data_obj[variable])                               # How to view the variable information (netcdf obj)
        print(data_obj[variable][:])                            # Access the numpy array inside the variable (array)
        print(data_obj[variable].dimensions)                    # Get the dimensions associated with a variable (tuple)
        print(data_obj[variable].__dict__)                      # How to get the attributes of a variable (dictionary)
        print(data_obj[variable].__dict__['standard_name'])     # How to access a specific attribute (also long_name)
        name = data_obj[variable].__dict__['long_name'].replace('_', ' ').capitalize()
        variables[name] = variable                              # Create a Full-Short variable name dictionary
    pprint.pprint(variables)

    for dimension in data_obj.dimensions.keys():
        print(data_obj.dimensions[dimension].size)              # print the size of a dimension

    data_obj.sync()                                             # if you wrote data to the file, save it to the disc
    data_obj.close()                                            # close the file connection to the file

    return


def variablebounds(file_path):
    """
    Description: Makes a dictionary of variable names with a string 'min,max' of the smallest and largest values
    Params: A dictionary object from the AJAX-ed JSON object that contains coordinates and the variable name.
    Author: Riley Hales, 2019
    Dependencies: netcdf4, numpy
    """
    import netCDF4
    import numpy
    bounds = {}

    data_obj = netCDF4.Dataset(file_path, 'r', clobber=False, diskless=True, persist=False)
    print(data_obj)

    for variable in data_obj.variables.keys():
        min = numpy.min(data_obj[variable][:])
        max = numpy.max(data_obj[variable][:])
        bounds[variable] = str(min) + ',' + str(max)
    print(bounds)
    return bounds
