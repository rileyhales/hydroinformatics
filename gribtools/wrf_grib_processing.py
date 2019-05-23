import netCDF4, xarray, cfgrib
# conda install -c conda-forge cfgrib

gribfile = '/Users/rileyhales/thredds/ffgs/wrf_20190522/wrf_20190522_f48.grib2'

gribobj = xarray.open_dataset(gribfile, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
print(gribobj['tp'])

# cfgriboption = cfgrib.open_file(gribfile)


"""
filter_by_keys={'typeOfLevel': 'meanSea'}
filter_by_keys={'typeOfLevel': 'unknown'}
filter_by_keys={'typeOfLevel': 'surface'}
filter_by_keys={'typeOfLevel': 'isobaricInhPa'}
filter_by_keys={'typeOfLevel': 'isobaricLayer'}
filter_by_keys={'typeOfLevel': 'heightAboveGroundLayer'}
filter_by_keys={'typeOfLevel': 'heightAboveGround'}
filter_by_keys={'typeOfLevel': 'cloudBase'}
filter_by_keys={'typeOfLevel': 'heightAboveSea'}
filter_by_keys={'typeOfLevel': 'pressureFromGroundLayer'}
filter_by_keys={'typeOfLevel': 'isothermal'}
filter_by_keys={'typeOfLevel': 'hybrid'}
filter_by_keys={'typeOfLevel': 'depthBelowLandLayer'}
"""