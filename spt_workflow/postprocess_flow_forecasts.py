"""
postprocess_flow_forecasts.py

Author: Riley Hales
Copyright March 2020
License: BSD 3 Clause

Identifies flows forecasted to experience a return period level flow on streams from a preprocessed list of stream
COMID's in each region
"""
import datetime
import glob
import logging
import os
import sys

import numpy as np
import pandas as pd
import xarray
import netCDF4 as nc


def merge_forecast_qout_files(rapidio_region_output):
    # pick the most recent date, append to the file path
    recent_date = sorted(os.listdir(rapidio_region_output))
    recent_date = recent_date[-1]
    qout_folder = os.path.join(rapidio_region_output, recent_date)
    # list the forecast files
    prediction_files = sorted(glob.glob(os.path.join(qout_folder, 'Qout*.nc')))

    # merge them into a single file joined by ensemble number
    ensemble_index_list = []
    qout_datasets = []
    for forecast_nc in prediction_files:
        ensemble_index_list.append(int(os.path.basename(forecast_nc)[:-3].split("_")[-1]))
        qout_datasets.append(xarray.open_dataset(forecast_nc).Qout)
    return xarray.concat(qout_datasets, pd.Index(ensemble_index_list, name='ensemble')), qout_folder


def check_for_return_period_flow(largeflows_df, forecasted_flows_df, stream_order, rp_data):
    max_flow = max(forecasted_flows_df['means'])

    # temporary dates
    date_r2 = ''
    date_r10 = ''
    date_r20 = ''
    date_r25 = ''
    date_r50 = ''
    date_r100 = ''

    # retrieve return period flow levels from dataframe
    r2 = float(rp_data['return_period_2'].values[0])
    r10 = float(rp_data['return_period_10'].values[0])
    r20 = float(rp_data['return_period_20'].values[0])
    # r25 = float(rp_data['return_period_25'].values[0])
    # r50 = float(rp_data['return_period_50'].values[0])
    # r100 = float(rp_data['return_period_100'].values[0])

    # then compare the timeseries to the return period thresholds
    if max_flow >= r2:
        date_r2 = get_time_of_first_exceedence(forecasted_flows_df, r2)
    # if the flow is not larger than the smallest return period, return the dataframe without appending anything
    else:
        return largeflows_df

    # check the rest of the return period flow levels
    if max_flow >= r10:
        date_r10 = get_time_of_first_exceedence(forecasted_flows_df, r10)
    if max_flow >= r20:
        date_r20 = get_time_of_first_exceedence(forecasted_flows_df, r20)
    # if max_flow >= r25:
    #     date_r25 = get_time_of_first_exceedence(forecasted_flows_df, r25)
    # if max_flow >= r50:
    #     date_r50 = get_time_of_first_exceedence(forecasted_flows_df, r50)
    # if max_flow >= r100:
    #     date_r100 = get_time_of_first_exceedence(forecasted_flows_df, r100)

    return largeflows_df.append({
        'comid': rp_data.index,
        'stream_order': stream_order,
        'stream_lat': rp_data['lat'],
        'stream_lon': rp_data['lon'],
        'max_flow': max_flow,
        'date_r2': date_r2,
        'date_r10': date_r10,
        'date_r20': date_r20,
        # 'date_r25': date_r25,
        # 'date_r50': date_r50,
        # 'date_r100': date_r100,
    }, ignore_index=True)


def get_time_of_first_exceedence(forecasted_flows_df, flow):
    # replace the flows that are too small (don't exceed the return period)
    forecasted_flows_df[forecasted_flows_df.means < flow] = np.nan
    daily_flows = forecasted_flows_df.dropna()
    return daily_flows['times'].values[0]


def postprocess_region(region, rapidio, historical_sim, forecast_records):
    # build the propert directory paths
    rapidio_region_input = os.path.join(rapidio, 'input', region)
    rapidio_region_output = os.path.join(rapidio, 'output', region)

    # make the pandas dataframe to store the summary info
    largeflows = pd.DataFrame(columns=[
        'comid', 'stream_order', 'stream_lat', 'stream_lon', 'max_flow', 'date_r2', 'date_r10', 'date_r20'])
    # , 'date_r25', 'date_r50', 'date_r100'])

    # merge the most recent forecast files into a single xarray dataset
    merged_forecasts, qout_folder = merge_forecast_qout_files(rapidio_region_output)

    # collect the times and comids from the forecasts
    times = pd.to_datetime(pd.Series(merged_forecasts.time))
    comids = pd.Series(merged_forecasts.rivid)
    tomorrow = times[0] + pd.Timedelta(days=1)
    year = times[0].strftime("%Y")

    # read the return period file
    return_period_file = glob.glob(os.path.join(historical_sim, region, 'return_period*.nc'))[0]
    return_period_data = xarray.open_dataset(return_period_file).to_dataframe()

    # read the list of large streams
    stream_list = os.path.join(rapidio_region_input, 'large_str-' + region + '.csv')
    large_streams_df = pd.read_csv(stream_list)
    large_list = large_streams_df['COMID'].to_list()

    # identify the netcdf used to store the forecast record
    forecast_record_file = find_forecast_record_netcdf(region, forecast_records, qout_folder, year)
    record_times = list(forecast_record_file.variables['time'][:])

    # message for tracking the workflow
    logging.info('beginning to iterate over the comids')

    # now process the mean flows for each river in the region
    for comid in comids:
        # compute the timeseries of average flows
        means = np.array(merged_forecasts.sel(rivid=comid)).mean(axis=0)
        # put it in a dataframe with the times series
        forecasted_flows = times.to_frame(name='times').join(pd.Series(means, name='means')).dropna()

        # select flows in 1st day and save them to the forecast record
        first_day_flows = forecasted_flows[forecasted_flows.times < tomorrow]
        comid_index = list(forecast_record_file.variables['rivid'][:]).index(comid)
        day_times = first_day_flows['times']
        day_flows = first_day_flows['means']
        for time, flow in zip(day_times, day_flows):
            idx = record_times.index(datetime.datetime.timestamp(time))
            forecast_record_file.variables['Qout'][comid_index, idx] = flow

        # if stream order is larger than 2, check if it needs to be included on the return periods summary csv
        if comid in large_list:
            order = large_streams_df[large_streams_df.COMID == comid]['order_']
            rp_data = return_period_data[return_period_data.index == comid]
            largeflows = check_for_return_period_flow(largeflows, forecasted_flows, order, rp_data)

    # close the forecast_record_file
    forecast_record_file.sync()
    forecast_record_file.close()

    # now save the return periods summary csv to the right output directory
    largeflows.to_csv(os.path.join(qout_folder, 'forecasted_return_periods_summary.csv'), index=False)

    return


def find_forecast_record_netcdf(region, forecast_records, qout_folder, year):
    record_path = os.path.join(forecast_records, region)
    if not os.path.exists(record_path):
        os.mkdir(record_path)
    record_path = os.path.join(record_path, 'forecast_record-' + year + '-' + region + '.nc')
    # if there isn't a forecast record for this year
    if not os.path.exists(record_path):
        # using a forecast file as a reference
        reference = glob.glob(os.path.join(qout_folder, 'Qout*.nc'))[0]
        reference = nc.Dataset(reference)
        # make a new record file
        record = nc.Dataset(record_path, 'w')
        # copy the right dimensions and variables
        record.createDimension('time', None)
        record.createDimension('rivid', reference.dimensions['rivid'].size)
        record.createVariable('time', reference.variables['time'].dtype, dimensions=('time',))
        record.createVariable('lat', reference.variables['lat'].dtype, dimensions=('rivid',))
        record.createVariable('lon', reference.variables['lon'].dtype, dimensions=('rivid',))
        record.createVariable('rivid', reference.variables['rivid'].dtype, dimensions=('rivid',))
        record.createVariable('Qout', reference.variables['Qout'].dtype, dimensions=('rivid', 'time'))
        # and also prepopulate the lat, lon, and rivid fields
        record.variables['rivid'][:] = reference.variables['rivid'][:]
        record.variables['lat'][:] = reference.variables['lat'][:]
        record.variables['lon'][:] = reference.variables['lon'][:]
        # calculate the time variable's steps 'hours since YYYY0101 00:00:00' hours since midnight on new years day
        date = datetime.datetime(year=int(year), month=1, day=1, hour=0, minute=0, second=0)
        end = int(year) + 1
        forecast_timesteps = []
        while date.year < end:
            forecast_timesteps.append(datetime.datetime.timestamp(date))
            date = date + datetime.timedelta(hours=3)
        record.variables['time'][:] = forecast_timesteps
        record.close()

    return nc.Dataset(record_path, mode='a')


if __name__ == '__main__':
    """
    arg1 = path to the rapid-io directory where the input and output directory are located. You need the input
        directory because thats where the large_str-region-name.csv file is located. outputs contain the forecst outputs 
    arg2 = path to directory where the historical data are stored. the folder that contains 1 folder for each region.
    arg3 = path to the directory where the 1day forecasts are saved. the folder that contains 1 folder for each region.
    arg4 = path to the logs directory
    """
    # accept the arguments
    rapidio = sys.argv[1]
    historical_sim = sys.argv[2]
    forecast_records = sys.argv[3]
    logs_dir = sys.argv[4]

    # rapidio = '/Users/rileyhales/SpatialData/SPT/rapid-io/'
    # historical_sim = '/Users/rileyhales/SpatialData/SPT/historical/'
    # forecast_records = '/Users/rileyhales/SpatialData/SPT/forecastrecords/'
    # logs_dir = '/Users/rileyhales/SpatialData/SPT/logs/'

    # list of regions to be processed based on their forecasts
    regions = os.listdir(os.path.join(rapidio, 'input'))

    # start logging
    start = datetime.datetime.now()
    log = os.path.join(logs_dir, 'postprocess_forecasts-' + start.strftime("%Y%m%d"))
    logging.basicConfig(filename=log, filemode='w', level=logging.INFO)
    logging.info('postprocess_flow_forecasts.py initiated ' + start.strftime("%c"))

    for region in regions:
        try:
            # log start messages
            logging.info('')
            logging.info('WORKING ON ' + region)
            logging.info('elapsed time: ' + str(datetime.datetime.now() - start))
            # attempt to postprocess the region
            postprocess_region(region, rapidio, historical_sim, forecast_records)
        except Exception as e:
            logging.info(e)
            logging.info('region failed at ' + datetime.datetime.now().strftime("%c"))

    logging.info('')
    logging.info('Finished at ' + datetime.datetime.now().strftime("%c"))
    logging.info('Total elapsed time: ' + str(datetime.datetime.now() - start))
