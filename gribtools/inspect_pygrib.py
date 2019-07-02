import pygrib

file = '/Users/rileyhales/thredds/gribs/2019070118.grb'
gribs = pygrib.open(file)
gribs.seek(0)                       # go to the start of the file (it reads like a python file object

# iterating through each element in the grib file
for grb in gribs:
    print(grb)                      # print a summary of information about the grib
    print(grb.keys())               # get a list of all the attribute keys for that variable
    print(grb.values)               # the numpy array of data comes with the values key, not data
    print(grb.name)                 # some common and useful attributes of each variable
    print(grb.shortName)
    print(grb.minimum)
    print(grb.maximum)
    print(grb.topLevel)
    print(grb.bottomLevel)
    print(grb.level)

# getting information directly by looking up data by its indexed number (see print(grb) above)
print(gribs[158])
print(gribs[150].keys())            # all the attributes, see previous for more examples


# filter the grib by specifying values of attributes to pick
some_gribs = gribs(typeOfLevel='depthBelowLandLayer')

# alternate format for similar filtering options
grb = gribs.select(name='Total Cloud Cover')
for g in grb:
    print(g)
