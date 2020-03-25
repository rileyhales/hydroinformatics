import os
import glob
import netCDF4 as nc
import xarray
import pandas as pd
import numpy as np


def make_one_ensemble_summary(qout_file, rp_file, csv_save_dir):
    """
    Creates a csv file with the columns:
        comid, stream_lat, stream_lon, return_period_exceeded, flow
    For example:
        10000, 40, -30, 25, 150
    indicates that comid 10000, located at lat 40 and lon -30, surpassed it's 25 year return period flow with a flow of
    150 cubic meters per second.

    Args:
        qout_file: the full path to a Qout file produced by the ECMWF rapid workflow
        rp_file: the full path to the Gumbel return periods file for the same region
        csv_save_dir: the directory where to save the csv
    """
    # get the comids in qout file
    qout_data = nc.Dataset(qout_file, 'r')
    comids_qout = qout_data['rivid'][:]

    return_period_nc = nc.Dataset(rp_file, 'r')
    comids_rp = list(return_period_nc.variables['rivid'][:])
    # r100_thresholds = return_period_nc.variables['return_period_100'][:]
    # r50_thresholds = return_period_nc.variables['return_period_50'][:]
    # r25_thresholds = return_period_nc.variables['return_period_25'][:]
    r20_thresholds = return_period_nc.variables['return_period_20'][:]
    r10_thresholds = return_period_nc.variables['return_period_10'][:]
    r2_thresholds = return_period_nc.variables['return_period_2'][:]
    lat = return_period_nc.variables['lat'][:]
    lon = return_period_nc.variables['lon'][:]
    return_period_nc.close()

    largeflows = pd.DataFrame(columns=['comid', 'stream_lat', 'stream_lon', 'return_period', 'flow'])

    for index_qout, comid in enumerate(comids_qout):
        index_rp = comids_rp.index(comid)
        maxflow = max(qout_data['Qout'][index_rp])

        # if maxflow >= r100_thresholds[index_rp]:
        #     rp = 100
        # elif maxflow >= r50_thresholds[index_rp]:
        #     rp = 50
        # elif maxflow >= r25_thresholds[index_rp]:
        #     rp = 25
        if maxflow >= r20_thresholds[index_rp]:
            rp = 20
        elif maxflow >= r10_thresholds[index_rp]:
            rp = 10
        elif maxflow >= r2_thresholds[index_rp]:
            rp = 2
        else:
            continue
        largeflows = largeflows.append({
            'comid': int(comid),
            'stream_lat': lat[index_rp],
            'stream_lon': lon[index_rp],
            'return_period': rp,
            'flow': maxflow,
        }, ignore_index=True)

    largeflows.to_csv(os.path.join(csv_save_dir, 'forecasted_return_periods_summary.csv'))
    return


def get_time_of_first_exceedence(flow, means, times):
    # replace the flows that are too small (don't exceed the return period)
    means[means < flow] = np.nan
    # convert to list
    means = list(means)
    # return the time at the same index as the first non np.nan flow (uses i>0 because of how nan works in logic)
    return times[means.index(next(i for i in means if i > 0))]


def make_forecasted_flow_summary(qout_folder, rp_file):
    # get list of prediction files
    prediction_files = sorted(glob.glob(os.path.join(qout_folder, 'Qout*.nc')))

    # merge them into a single file joined by ensemble number
    ensemble_index_list = []
    qout_datasets = []
    for forecast_nc in prediction_files:
        ensemble_index_list.append(int(os.path.basename(forecast_nc)[:-3].split("_")[-1]))
        qout_datasets.append(xarray.open_dataset(forecast_nc).Qout)
    merged_ds = xarray.concat(qout_datasets, pd.Index(ensemble_index_list, name='ensemble'))

    # collect the times and comids from the forecasts
    times = list(merged_ds.time)
    comids_qout = list(merged_ds.rivid)

    # read the return period file
    return_period_nc = nc.Dataset(rp_file, 'r')
    comids_rp = list(return_period_nc.variables['rivid'][:])
    # r100_thresholds = return_period_nc.variables['return_period_100'][:]
    # r50_thresholds = return_period_nc.variables['return_period_50'][:]
    # r25_thresholds = return_period_nc.variables['return_period_25'][:]
    r20_thresholds = return_period_nc.variables['return_period_20'][:]
    r10_thresholds = return_period_nc.variables['return_period_10'][:]
    r2_thresholds = return_period_nc.variables['return_period_2'][:]
    lat = return_period_nc.variables['lat'][:]
    lon = return_period_nc.variables['lon'][:]
    return_period_nc.close()

    # make the pandas dataframe to store the summary info
    largeflows = pd.DataFrame(columns=['comid', 'stream_lat', 'stream_lon', 'max_flow', 'date_r2'])  # , 'date_r10', 'date_r20', 'date_r25', 'date_r50', 'date_r100'])

    # for each comid in the forecast
    for index_qout, comid in enumerate(comids_qout):
        # produce a 1D array containing the timeseries average flow from all ensembles on each forecast timestep
        means = np.array(merged_ds.sel(rivid=comid)).mean(axis=0)
        max_flow = max(means)

        # determine the index of comid in the return periods array
        index_rp = comids_rp.index(comid)

        # reset the variables
        date_r2 = np.nan
        date_r10 = np.nan
        date_r20 = np.nan
        date_r25 = np.nan
        date_r50 = np.nan
        date_r100 = np.nan

        # then compare the timeseries to the return period thresholds
        # if max_flow >= r100_thresholds[index_rp]:
        #     date_r100 = get_time_of_first_exceedence(r100_thresholds[index_rp], means, times)
        # if max_flow >= r50_thresholds[index_rp]:
        #     date_r50 = get_time_of_first_exceedence(r50_thresholds[index_rp], means, times)
        # if max_flow >= r25_thresholds[index_rp]:
        #     date_r25 = get_time_of_first_exceedence(r25_thresholds[index_rp], means, times)
        if max_flow >= r20_thresholds[index_rp]:
            date_r20 = np.datetime_as_string(get_time_of_first_exceedence(r20_thresholds[index_rp], means, times))
        if max_flow >= r10_thresholds[index_rp]:
            date_r10 = np.datetime_as_string(get_time_of_first_exceedence(r10_thresholds[index_rp], means, times))
        if max_flow >= r2_thresholds[index_rp]:
            date_r2 = np.datetime_as_string(get_time_of_first_exceedence(r2_thresholds[index_rp], means, times))
        else:
            continue
        largeflows = largeflows.append({
            'comid': int(comid),
            'stream_lat': lat[index_rp],
            'stream_lon': lon[index_rp],
            'max_flow': max_flow,
            'date_r2': date_r2,
            'date_r10': date_r10,
            'date_r20': date_r20,
            # 'date_r25': date_r25,
            # 'date_r50': date_r50,
            # 'date_r100': date_r100,
        }, ignore_index=True)

    largeflows.to_csv(os.path.join(qout_folder, 'forecasted_return_periods_summary.csv'))

    return


make_forecasted_flow_summary('/Users/rileyhales/SpatialData/SPT/20200323.0', '/Users/rileyhales/SpatialData/SPT/return_periods_erai_t511_24hr_19800101to20141231.nc')
