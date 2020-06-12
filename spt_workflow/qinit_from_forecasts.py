import glob
import xarray
import numpy as np
import pandas as pd
import os


output_folder = '/Users/riley/spatialdata/rapid-io/output/'
for region in os.listdir(output_folder):
    print(f'started {region}')
    prediction_files = sorted(glob.glob(os.path.join(output_folder, region, '20200610.0', 'Qout*.nc')))
    # merge them into a single file joined by ensemble number
    ensemble_index_list = []
    qout_datasets = []
    for forecast_nc in prediction_files:
        ensemble_index_list.append(int(os.path.basename(forecast_nc)[:-3].split("_")[-1]))
        qout_datasets.append(xarray.open_dataset(forecast_nc).Qout)
    ds = xarray.concat(qout_datasets, pd.Index(ensemble_index_list, name='ensemble'))
    qinit_path = os.path.join(output_folder, region, '20200610.0', 'Qinit_20200610t00.csv')
    pd.DataFrame(np.nanmean(ds.data[:, :, 24], axis=0)[::-1]).to_csv(qinit_path, index=False, header=False)
    print(f'finished {region}')
