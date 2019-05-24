import xarray, cfgrib

# conda install -c conda-forge cfgrib

path = '/Users/rileyhales/thredds/gfs/gribs/2019052412/gfs_2019052412_006.grb'
obj = xarray.open_dataset(path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
print(obj)
print(obj.coords['latitude'].data)
print(obj.coords['longtiude'].data)

for key in enumerate(obj.keys()):
    print(key[1])

obj.to_netcdf('pleasework.nc', mode='w')

print(obj.values())
print(obj.variables)

for variable in obj.variables:
    print(variable)
