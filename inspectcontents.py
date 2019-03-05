import netCDF4, pprint

filepath = r'/Users/rileyhales/thredds/malaria/LIS_HIST_20070402.nc'

data_obj = netCDF4.Dataset(filepath, 'r', clobber=False, diskless=True, persist=False)

print("This is your netcdf object")
pprint.pprint(data_obj)

print("There are " + str(len(data_obj.variables)) + " variables")       # The number of variables
print("There are " + str(len(data_obj.dimensions)) + " dimensions")     # The number of dimensions


variables = {}
print("Detailed view of each variable")
for variable in data_obj.variables.keys():
    if variable == 'latitude' or variable == 'longitude' or variable.startswith("Tair_f_tavg_"):
        continue
    print(variable)                                         # the string name of the variable
    print(data_obj[variable])                               # How to view the variable
    print(data_obj[variable].__dict__)                      # How to get the attributes of a variable
    print(data_obj[variable].__dict__['standard_name'])     # How to access a specific attribute

                                                            # Create a Full-Short variable name dictionary
    name = data_obj[variable].__dict__['standard_name'].replace('_', ' ').capitalize()
    variables[name] = variable
pprint.pprint(variables)
