import netCDF4, pprint

filepath = r''

data_obj = netCDF4.Dataset(filepath, 'r', clobber=False, diskless=True, persist=False)

print("This is your netcdf object")
pprint.pprint(data_obj)

print("There are " + str(len(data_obj.variables)) + " variables")       # The number of variables
print("There are " + str(len(data_obj.dimensions)) + " dimensions")     # The number of dimensions


variables = {}
print("Detailed view of each variable")
for variable in data_obj.variables.keys():                  # .keys() gets the name of each variable
    print(variable)                                         # The string name of the variable
    print(data_obj[variable])                               # How to view the variable
    print(data_obj[variable].__dict__)                      # How to get the attributes of a variable
    print(data_obj[variable].__dict__['standard_name'])     # How to access a specific attribute
    name = data_obj[variable].__dict__['standard_name'].replace('_', ' ').capitalize()
    variables[name] = variable                              # Create a Full-Short variable name dictionary
pprint.pprint(variables)
