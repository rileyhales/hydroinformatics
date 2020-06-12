import netCDF4 as nc
import pandas as pd
import os


fp ='/Users/riley/code/gsp_rest_api/output/forecast-records/japan-geoglows/forecast_record-2020-japan-geoglows.nc'
ds = nc.Dataset(fp)
df = pd.DataFrame(ds['Qout'][:, -1])
region = os.path.basename(os.path.dirname(fp))
df.to_csv('/Users/riley/Qinit_20200611t00.csv', index=False, header=False)