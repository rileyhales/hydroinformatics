"""
Copyright Riley Hales
April 6 2020
"""
import netCDF4
import numpy as np
import os
import sys
import logging
import datetime


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
    new_nc.createVariable('Qout_min', datatype='f4', dimensions=('time', 'rivid'))
    new_nc.createVariable('Qout_mean', datatype='f4', dimensions=('time', 'rivid'))
    new_nc.createVariable('Qout_max', datatype='f4', dimensions=('time', 'rivid'))

    # configure the time variable
    new_nc.variables['time'][:] = range(new_nc.dimensions['time'].size)
    new_nc.variables['time'].__dict__['units'] = 'days since 1979-01-01 00:00:00+00:00'
    new_nc.variables['time'].__dict__['calendar'] = 'gregorian'

    # configure the rivid variable
    logging.info('populating the rivid variable')
    new_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]

    # collect information used to create iteration parameters
    num_rivers = source_nc.dimensions['rivid'].size
    number_hours = source_nc.variables['time'].shape[0] - 1
    number_days = number_hours / 24
    hours_in_day = 24
    print(num_rivers)

    # create a set of indices for slicing the array in larger groups
    pairs_of_indices = list(range(num_rivers))
    index_pairs = []
    while len(pairs_of_indices) > 0:
        arr = pairs_of_indices[:write_frequency]
        index_pairs.append((arr[0], arr[-1]))
        pairs_of_indices = pairs_of_indices[write_frequency:]
    number_groups = len(pairs_of_indices)

    for group_num, pairs in enumerate(index_pairs):
        start_index = pairs[0]
        end_index = pairs[1]
        logging.info('Started group ' + str(group_num) + '/' + str(number_groups) + ' -- ' + datetime.datetime.utcnow().strftime("%c"))

        # on the sample outputs the dimensions are time, rivid
        # arr = np.asarray(source_nc.variables['Qout'][0:number_hours, start_index:end_index])
        # on the rapid docker image, the dimensions are rivid, time, i think
        arr = np.asarray(source_nc.variables['Qout'][start_index:end_index, 0:number_hours])
        arr = np.transpose(arr)
        print(arr.shape)

        minlist = []
        meanlist = []
        maxlist = []

        # if the array is at least 'size' long
        for day_flows in np.split(arr, number_days):
            # take the first 'size' pieces
            # get the min, mean, max and put them into a list
            minlist.append(day_flows.min(axis=0))
            # print(minlist)
            meanlist.append(day_flows.mean(axis=0))
            maxlist.append(day_flows.max(axis=0))
            # drop the first 'size' elements in the array
            arr = arr[hours_in_day:]

        min_arr = np.asarray(minlist)
        mean_arr = np.asarray(meanlist)
        max_arr = np.asarray(maxlist)

        print(min_arr.shape)
        print(mean_arr.shape)
        print(max_arr.shape)

        new_nc.variables['Qout_min'][:, start_index:end_index] = min_arr
        logging.info('  writing Qmean group of 500')
        new_nc.variables['Qout_mean'][:, start_index:end_index] = mean_arr
        logging.info('  writing Qmax group of 500')
        new_nc.variables['Qout_max'][:, start_index:end_index] = max_arr
        new_nc.sync()

    # close the new netcdf
    new_nc.close()
    source_nc.close()

    logging.info('')
    logging.info('FINISHED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))
    return newfilepath


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
    aggregate_by_day(sys.argv[1], write_frequency=1000)
