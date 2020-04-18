"""
Copyright Riley Hales
April 6 2020
"""
import netCDF4
import xarray
import numpy as np
import os
import pandas as pd
import sys
import logging
import datetime
import plotly.graph_objs as go


def aggregate_by_day(path_Qout, write_frequency=500):
    # sort out the file paths
    if not os.path.isfile(path_Qout):
        raise FileNotFoundError('Qout file not found at this path')
    newfilepath = os.path.join(os.path.dirname(path_Qout), 'DailyAggregated_' + os.path.basename(path_Qout) + '4')

    # read the netcdfs
    source_nc = netCDF4.Dataset(filename=path_Qout, mode='r')
    new_nc = netCDF4.Dataset(filename=newfilepath, mode='w')

    # create rivid and time dimensions
    logging.info('creating new netcdf variables/dimensions')
    new_nc.createDimension('rivid', size=source_nc.dimensions['rivid'].size)
    new_nc.createDimension('time', size=source_nc.dimensions['time'].size // 24)
    # create rivid and time variables
    new_nc.createVariable('rivid', datatype='f4', dimensions=('rivid',))
    new_nc.createVariable('time', datatype='f4', dimensions=('time',))
    # create the variables for the flows
    # new_nc.createVariable('Qout_min', datatype='f4', dimensions=('time', 'rivid'))
    new_nc.createVariable('Qout', datatype='f4', dimensions=('time', 'rivid'))
    # new_nc.createVariable('Qout_max', datatype='f4', dimensions=('time', 'rivid'))

    # configure the time variable
    new_nc.variables['time'][:] = range(new_nc.dimensions['time'].size)
    new_nc.variables['time'].__dict__['units'] = 'days since 1979-01-01 00:00:00+00:00'
    new_nc.variables['time'].__dict__['calendar'] = 'gregorian'

    # configure the rivid variable
    new_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]

    # collect information used to create iteration parameters
    num_rivers = source_nc.dimensions['rivid'].size
    number_hours = source_nc.variables['time'].shape[0]
    if number_hours == 350641:
        logging.info('----WARNING---- TIME 350641 (expected 350640)')
        exact = False
    elif number_hours == 350640:
        exact = True
    else:
        raise RuntimeError('unexpected length of times found.')
    number_days = number_hours / 24
    logging.info('number of rivers: ' + str(num_rivers))

    # create a set of indices for slicing the array in larger groups
    indices = list(range(num_rivers))
    index_pairs = []
    while len(indices) > 0:
        arr = indices[:write_frequency]
        index_pairs.append((arr[0], arr[-1]))
        indices = indices[write_frequency:]
    number_groups = len(index_pairs)

    for group_num, pairs in enumerate(index_pairs):
        start_index = pairs[0]
        end_index = pairs[1]
        logging.info('Started group ' + str(group_num) + '/' + str(number_groups) + ' -- ' + datetime.datetime.utcnow().strftime("%c"))

        # depending on the version of rapid used, the dimension order is different
        if source_nc.variables['Qout'].dimensions == ('time', 'rivid'):
            if exact:
                arr = np.asarray(source_nc.variables['Qout'][:, start_index:end_index])
            elif not exact:
                arr = np.asarray(source_nc.variables['Qout'][0:number_hours, start_index:end_index])
        elif source_nc.variables['Qout'].dimensions == ('rivid', 'time'):
            if exact:
                arr = np.transpose(np.asarray(source_nc.variables['Qout'][start_index:end_index, :]))
            elif not exact:
                arr = np.transpose(np.asarray(source_nc.variables['Qout'][start_index:end_index, 0:number_hours]))
        else:
            logging.info('Unable to recognize the dimension order, exiting')
            exit()

        logging.info(arr.shape)

        # min_arr = []
        mean_arr = []
        # max_arr = []

        # if the array is at least 'size' long
        for day_flows in np.split(arr, number_days):
            # min_arr.append(day_flows.min(axis=0))
            mean_arr.append(day_flows.mean(axis=0))
            # max_arr.append(day_flows.max(axis=0))

        # min_arr = np.asarray(min_arr)
        mean_arr = np.asarray(mean_arr)
        # max_arr = np.asarray(max_arr)

        # logging.info(min_arr.shape)
        logging.info(mean_arr.shape)
        # logging.info(max_arr.shape)

        # logging.info('  writing Qmin group')
        # new_nc.variables['Qout_min'][:, start_index:end_index] = min_arr
        logging.info('  writing Qout group')
        new_nc.variables['Qout'][:, start_index:end_index] = mean_arr
        # logging.info('  writing Qmax group')
        # new_nc.variables['Qout_max'][:, start_index:end_index] = max_arr
        new_nc.sync()

    # close the new netcdf
    new_nc.close()
    source_nc.close()

    logging.info('')
    logging.info('FINISHED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))
    return newfilepath


def validate_aggregated_rivid(path_Qout, path_Aggregated_qout, rivid=None):
    old_xar = xarray.open_dataset(path_Qout)
    new_xar = xarray.open_dataset(path_Aggregated_qout)

    if not rivid:
        rivid = int(np.random.choice(new_xar.variables['rivid'], 1))

    old_times = pd.to_datetime(pd.Series(old_xar.sel(rivid=rivid).time))
    oldflow = np.asarray(old_xar.sel(rivid=rivid).Qout)
    new_times = np.asarray(new_xar.sel(rivid=rivid).time)
    newmin = np.asarray(new_xar.sel(rivid=rivid).Qout_min)
    newmean = np.asarray(new_xar.sel(rivid=rivid).Qout_mean)
    newmax = np.asarray(new_xar.sel(rivid=rivid).Qout_max)

    start = datetime.datetime(year=1979, month=1, day=1)
    new_times = [start + datetime.timedelta(days=int(i)) for i in new_times]

    new_scatter_min = go.Scatter(
        name='new_data_min',
        x=new_times,
        y=list(newmin),
        line={'color': 'yellow'}
    )
    new_scatter_mean = go.Scatter(
        name='new_data_mean',
        x=new_times,
        y=list(newmean),
        line={'color': 'black'}
    )
    new_scatter_max = go.Scatter(
        name='new_data_max',
        x=new_times,
        y=list(newmax),
        line={'color': 'blue'}
    )
    old_scatter = go.Scatter(
        name='old_flow',
        x=old_times,
        y=list(oldflow),
        line={'color': 'red'}
    )
    layout = go.Layout(
        title='Aggregation Comparison',
        xaxis={'title': 'Date', 'range': [10000, 15000]},
        yaxis={'title': 'Streamflow (m<sup>3</sup>/s)'},
    )

    figure = go.Figure((new_scatter_min, new_scatter_mean, new_scatter_max, old_scatter), layout=layout)
    figure.show()

    return


# for running this script from the command line with a script
if __name__ == '__main__':
    """
    sys.argv[0] this script e.g. aggregate.py
    sys.argv[1] path to Qout file
    sys.argv[2] path to log file
    """
    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=sys.argv[2], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('ERA5 aggregation started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    aggregated_file = aggregate_by_day(sys.argv[1], write_frequency=1000)
    # validate_aggregated_rivid(sys.argv[1], aggregated_file)
