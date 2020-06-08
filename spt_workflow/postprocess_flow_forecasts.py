"""
postprocess_flow_forecasts.py

Author: Riley Hales
Copyright March 2020
License: BSD 3 Clause
Updated: June 2020

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

# todo make process_region into process_date which gets called by process_region, then you can pick whether to aggregate all days or none


def merge_forecast_qout_files(rapidio_region_output):
    # pick the most recent date, append to the file path
    recent_date = sorted(os.listdir(rapidio_region_output))
    while recent_date[-1].endswith('.csv'):
        recent_date.remove(recent_date[-1])
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
    date_r5 = ''
    date_r10 = ''
    date_r25 = ''
    date_r50 = ''
    date_r100 = ''

    # retrieve return period flow levels from dataframe
    r2 = float(rp_data['return_period_2'].values[0])
    r5 = float(rp_data['return_period_5'].values[0])
    r10 = float(rp_data['return_period_10'].values[0])
    r25 = float(rp_data['return_period_25'].values[0])
    r50 = float(rp_data['return_period_50'].values[0])
    r100 = float(rp_data['return_period_100'].values[0])

    # then compare the timeseries to the return period thresholds
    if max_flow >= r2:
        date_r2 = get_time_of_first_exceedence(forecasted_flows_df, r2)
    # if the flow is not larger than the smallest return period, return the dataframe without appending anything
    else:
        return largeflows_df

    # check the rest of the return period flow levels
    if max_flow >= r5:
        date_r5 = get_time_of_first_exceedence(forecasted_flows_df, r5)
    if max_flow >= r10:
        date_r10 = get_time_of_first_exceedence(forecasted_flows_df, r10)
    if max_flow >= r25:
        date_r25 = get_time_of_first_exceedence(forecasted_flows_df, r25)
    if max_flow >= r50:
        date_r50 = get_time_of_first_exceedence(forecasted_flows_df, r50)
    if max_flow >= r100:
        date_r100 = get_time_of_first_exceedence(forecasted_flows_df, r100)

    return largeflows_df.append({
        'comid': rp_data.index[0],
        'stream_order': stream_order,
        'stream_lat': float(rp_data['lat'].values),
        'stream_lon': float(rp_data['lon'].values),
        'max_forecasted_flow': round(max_flow, 2),
        'date_exceeds_return_period_2': date_r2,
        'date_exceeds_return_period_5': date_r5,
        'date_exceeds_return_period_10': date_r10,
        'date_exceeds_return_period_25': date_r25,
        'date_exceeds_return_period_50': date_r50,
        'date_exceeds_return_period_100': date_r100,
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
        'comid', 'stream_order', 'stream_lat', 'stream_lon', 'max_forecasted_flow', 'date_exceeds_return_period_2',
        'date_exceeds_return_period_5', 'date_exceeds_return_period_10', 'date_exceeds_return_period_25',
        'date_exceeds_return_period_50', 'date_exceeds_return_period_100'])

    # merge the most recent forecast files into a single xarray dataset
    logging.info('  merging forecasts')
    merged_forecasts, qout_folder = merge_forecast_qout_files(rapidio_region_output)

    # collect the times and comids from the forecasts
    logging.info('  reading info from forecasts')
    times = pd.to_datetime(pd.Series(merged_forecasts.time))
    comids = pd.Series(merged_forecasts.rivid)
    tomorrow = times[0] + pd.Timedelta(days=1)
    year = times[0].strftime("%Y")

    # read the return period file
    logging.info('  reading return period file')
    return_period_file = os.path.join(historical_sim, region, 'gumbel_return_periods.nc')
    return_period_data = xarray.open_dataset(return_period_file).to_dataframe()

    # read the list of large streams
    logging.info('  creating dataframe of large streams')
    stream_list = os.path.join(rapidio_region_input, 'large_str-' + region + '.csv')
    large_streams_df = pd.read_csv(stream_list)
    large_list = large_streams_df['COMID'].tolist()

    # store the first day flows in a huge array
    logging.info('  beginning to iterate over the comids')
    first_day_flows = []

    # now process the mean flows for each river in the region
    for comid in comids:
        # compute the timeseries of average flows
        means = np.array(merged_forecasts.sel(rivid=comid)).mean(axis=0)
        # put it in a dataframe with the times series
        forecasted_flows = times.to_frame(name='times').join(pd.Series(means, name='means')).dropna()
        # select flows in 1st day and save them to the forecast record
        first_day_flows.append(list(forecasted_flows[forecasted_flows.times < tomorrow]['means']))

        # if stream order is larger than 2, check if it needs to be included on the return periods summary csv
        if comid in large_list:
            order = int(large_streams_df[large_streams_df.COMID == comid]['order_'].values)
            rp_data = return_period_data[return_period_data.index == comid]
            largeflows = check_for_return_period_flow(largeflows, forecasted_flows, order, rp_data)

    # add the dataframe of forecasted flows to the forecast records file for this region
    logging.info('  updating the forecast records file')
    try:
        update_forecast_records(region, forecast_records, qout_folder, year, first_day_flows, times)
    except Exception as excp:
        logging.info('  unexpected error updating the forecast records')
        logging.info(excp)

    # now save the return periods summary csv to the right output directory
    largeflows.to_csv(os.path.join(qout_folder, 'forecasted_return_periods_summary.csv'), index=False)

    return


def update_forecast_records(region, forecast_records, qout_folder, year, first_day_flows, times):
    record_path = os.path.join(forecast_records, region)
    if not os.path.exists(record_path):
        os.mkdir(record_path)
    record_path = os.path.join(record_path, 'forecast_record-' + year + '-' + region + '.nc')

    # if there isn't a forecast record for this year, make one
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

        # set the time variable attributes so that the
        record.variables['time'].setncattr('units', 'hours since {0}0101 00:00:00'.format(year))

        # calculate the number of 3-hourly timesteps that will occur this year and store them in the time variable
        date = datetime.datetime(year=int(year), month=1, day=1, hour=0, minute=0, second=0)
        end = int(year) + 1
        timesteps = 0
        while date.year < end:
            date += datetime.timedelta(hours=3)
            timesteps += 1
        record.variables['time'][:] = [i * 3 for i in range(timesteps)]
        record.close()

    # open the record netcdf
    logging.info('  writing first day flows to forecast record netcdf')
    record_netcdf = nc.Dataset(record_path, mode='a')

    # figure out the right times
    startdate = datetime.datetime(year=int(year), month=1, day=1, hour=0, minute=0, second=0)
    record_times = [startdate + datetime.timedelta(hours=int(i)) for i in record_netcdf.variables['time'][:]]
    start_time_index = record_times.index(times[0])
    end_time_index = start_time_index + len(first_day_flows[0])
    # convert all those saved flows to a np array and write to the netcdf
    first_day_flows = np.asarray(first_day_flows)
    record_netcdf.variables['Qout'][:, start_time_index:end_time_index] = first_day_flows

    # save and close the netcdf
    record_netcdf.sync()
    record_netcdf.close()

    return


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
            logging.info('  elapsed time: ' + str(datetime.datetime.now() - start))
            # attempt to postprocess the region
            postprocess_region(region, rapidio, historical_sim, forecast_records)
        except Exception as e:
            logging.info(e)
            logging.info('      region failed at ' + datetime.datetime.now().strftime("%c"))

    logging.info('')
    logging.info('Finished at ' + datetime.datetime.now().strftime("%c"))
    logging.info('Total elapsed time: ' + str(datetime.datetime.now() - start))
