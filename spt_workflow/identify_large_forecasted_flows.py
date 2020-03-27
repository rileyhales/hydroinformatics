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
    means[means < flow] = 0
    # convert to list
    means = list(means)
    # return the time at the same index as the first non np.nan flow (uses i>0 because of how nan works in logic)
    return times[means.index(next(i for i in means if i > 0))]


def make_forecasted_flow_summary(comids_orders, qout_folder, rp_file):
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
    largeflows = pd.DataFrame(columns=['comid', 'stream_order', 'stream_lat', 'stream_lon', 'max_flow', 'date_r2'])  # , 'date_r10', 'date_r20', 'date_r25', 'date_r50', 'date_r100'])

    # for each comid in the forecast
    for comid, stream_order in comids_orders:
        # produce a 1D array containing the timeseries average flow from all ensembles on each forecast timestep
        means = np.array(merged_ds.sel(rivid=comid)).mean(axis=0)
        means = np.nan_to_num(means)
        means[means == np.nan] = -1
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
            'stream_order': int(stream_order),
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

    largeflows.to_csv(os.path.join(qout_folder, 'forecasted_return_periods_summary.csv'), index=False)

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
    logs_dir = os.path.join(large_stream_directory, 'logs')
    # if there isn't a logging directory, make it
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    log = os.path.join(logs_dir, start.strftime("%Y%m%d") + '-identify_large_forecasted_flows')
    logging.basicConfig(filename=log, filemode='w', level=logging.INFO)
    logging.info('identify_large_forecasted_flows.py initiated ' + start.strftime("%c"))

    # figure out which stream lists are in the directory
    stream_lists = glob.glob(os.path.join(large_stream_directory, 'large_str-*.csv'))

    if len(stream_lists) == 0:
        logging.info('No lists of streams identified. Exiting.')
        exit()

    for stream_list in stream_lists:
        try:
            # extract the region name, log messages
            region_name = os.path.basename(stream_list).replace('large_str-', '').replace('.csv', '')
            logging.info('')
            logging.info('Elapsed time: ' + str(datetime.datetime.now() - start))
            logging.info('identified large stream list for region: ' + region_name)

            # get a list of comids from the csv files
            df = pd.read_csv(stream_list)
            comids_orders = zip(df['COMID'].to_list(), df['order_'].to_list())

            # build the paths to the qout folder
            qout_folder = os.path.join(forecasts_directory, region_name)
            # if it doesn't exist, log it, skip it
            if not os.path.exists(qout_folder):
                logging.info('qout folder not found. skipping region.')
                continue
            # if it exists, check what dates are in it
            recent_date = sorted(os.listdir(os.path.join(forecasts_directory, region_name)))
            # if it can't find a date, log it, skip it
            if len(recent_date) == 0:
                logging.info('no date directories found. skipping.')
                continue
            # pick the most recent date, append to the file path
            recent_date = recent_date[-1]
            qout_folder = os.path.join(qout_folder, recent_date)
            logging.info('identified the most recent forecast date is ' + recent_date)

            # build the path to the historical data and return period file
            historical_path = os.path.join(historical_directory, region_name)
            # if it doesn't exist, log it, skip it
            if not os.path.exists(historical_path):
                logging.info('historical folder for this region not found. skipping region.')
                continue
            return_period_file = glob.glob(os.path.join(historical_path, 'return_period*.nc'))[0]

            # got all the information we need. run the summarization function
            make_forecasted_flow_summary(comids_orders, qout_folder, return_period_file)

        # if you get any other error, the problem was with the system or the file's data. log it to be debugged
        except Exception as e:
            logging.info('Exception occurred at ' + datetime.datetime.now().strftime("%c"))
            logging.info(e)

    # log when you finish
    end = datetime.datetime.now()
    logging.info('')
    logging.info('identify_large_forecasted_flows.py finished at ' + end.strftime('%c'))
    logging.info('total time elapsed: ' + str(end - start))
