"""
identify_large_forecasted_flows.py

Author: Riley Hales
Copyright March 2020
License: BSD 3 Clause

Identifies flows forecasted to experience a return period level flow on streams from a preprocessed list of stream
COMID's in each region
"""

import os
import logging
import datetime
import sys
import glob
import netCDF4 as nc
import xarray
import pandas as pd
import numpy as np


def get_time_of_first_exceedence(flow, means, times):
    # replace the flows that are too small (don't exceed the return period)
    means[means < flow] = np.nan
    # convert to list
    means = list(means)
    # return the time at the same index as the first non np.nan flow (uses i>0 because of how nan works in logic)
    return times[means.index(next(i for i in means if i > 0))]


def make_forecasted_flow_summary(comids, qout_folder, rp_file):
    # get list of prediction files
    prediction_files = sorted(glob.glob(os.path.join(qout_folder, 'Qout*.nc')))

    # merge them into a single file joined by ensemble number
    ensemble_index_list = []
    qout_datasets = []
    for forecast_nc in prediction_files:
        ensemble_index_list.append(int(os.path.basename(forecast_nc)[:-3].split("_")[-1]))
        qout_datasets.append(xarray.open_dataset(forecast_nc).Qout)
    merged_ds = xarray.concat(qout_datasets, pd.Index(ensemble_index_list, name='ensemble'))

    # collect the times from the forecasts
    times = list(merged_ds.time)

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
    for comid in comids:
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


if __name__ == '__main__':
    # arg1 = path to the directory with the large stream lists
    # arg2 = path to directory where forecasts get stored, the folder that contains 1 folder for each region
    # arg3 = path to directory where historical data are stored, the folder that contains 1 folder for each region

    # accept the arguments
    args = sys.argv
    large_stream_directory = args[1]
    forecasts_directory = args[2]
    historical_directory = args[3]

    # begin the logging
    start = datetime.datetime.now()
    log = os.path.join(large_stream_directory, 'logs', start.strftime("%Y%m%d-%H") + '_identify_large_forecasted_flows')
    logging.basicConfig(log, level=logging.INFO)
    logging.info('identify_large_forecasted_flows.py initiated ' + start.strftime("%c"))

    # figure out which stream lists are in the directory
    stream_lists = glob.glob(os.path.join(large_stream_directory, 'large_str-*.csv'))

    if len(stream_lists) == 0:
        logging.info('No lists of streams identified. Exiting.')
        exit()

    try:
        for stream_list in stream_lists:
            # extract the region name, log messages
            region_name = os.path.basename(stream_list).replace('large_str-', '').replace('.csv', '')
            logging.info('\nidentified large stream list for region: ' + region_name)
            logging.info('Elapsed time: ' + str(datetime.datetime.now() - start))

            # get a list of comids from the csv files
            comids = pd.read_csv(stream_list, header=None)[0].to_list()

            # build the paths to the qout folder
            recent_date = sorted(os.listdir(os.path.join(forecasts_directory, region_name)))
            if len(recent_date) == 0:
                logging.info('no date directories found. skipping.')
                pass
            qout_folder = os.path.join(forecasts_directory, region_name, recent_date[-1])
            if not os.path.exists(qout_folder):
                logging.info('qout folder not found. skipping region.')
                pass

            # build the path to the historical data and return period file
            historical_path = os.path.join(historical_directory, region_name)
            if not os.path.exists(historical_path):
                logging.info('historical folder for this region not found. skipping region.')
                pass
            return_period_file = glob.glob(os.path.join(historical_path, 'return_period*.nc'))[0]

            # since all files exist, run the summarization function
            make_forecasted_flow_summary(comids, qout_folder, return_period_file)

    except Exception as e:
        logging.info('Exception occured at ' + datetime.datetime.now().strftime("%c"))
        logging.info(e)

    logging.info('\nidentify_large_forecasted_flows.py finished at ' + datetime.datetime.now().strftime('%c'))
