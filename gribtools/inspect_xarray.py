import xarray, cfgrib
# conda install -c conda-forge cfgrib

"""
this example uses GFS grib data which is not formatted according to conventions for organization
you must specify a backend_kwarg to limit the data

most common error if you try to use cfgrib and xarray is a DatasetBuildError because the grib is not formatted by
the typical conventions. open it again with a try/except look and use the backend_kwargs option to filter_by_keys with 
the exception: except cfgrib.dataset.DatasetBuildError as error:
"""

levels = [
    'atmosphere',
    'depthBelowLandLayer',
    'heightAboveGround',  # nope
    'heightAboveGroundLayer',
    'heightAboveSea',
    'hybrid',
    'isothermZero',
    'isobaricInPa',
    'isobaricInhPa',  # nope
    'maxWind',
    'meanSea',
    'nominalTop',
    'potentialVorticity',
    'pressureFromGroundLayer',  # nope
    'sigma',
    'sigmaLayer',
    # 'surface',  # nope
    'tropopause',
    # 'unknown',  # nope
]
file = '/Users/rileyhales/thredds/2019062618.grb'
obj = xarray.open_dataset(
    file,
    engine='cfgrib',
    backend_kwargs={
        'filter_by_keys': {
            'typeOfLevel': 'name of measurement level',
            'cfVarName': 'name of variable',
            'stepType': 'time interval/measurement type',
            }
    }
)
print(list(obj.coords))                           # the coordinate variables
print(list(obj.data_vars))                        # the data variables
print(list(obj.variables))                        # all variables (both data + coord)
print(obj['variable_name'])                       # view the variable data including list of attributes
print(obj['variable_name'].attribute_name)        # get the value of an attribute of the variable
print(obj['variable_name'].data)                  # get the array of data contained at that variable

obj.to_netcdf('path/to/new/netcdf/file.nc')       # save as a netcdf file

obj.close()
