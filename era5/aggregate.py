import netCDF4
import os
import sys
import logging
import datetime
import statistics


def aggregate_by_day(path_Qout):
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

    # for each river read the whole time series
    num_rivers = source_nc.dimensions['rivid'].size
    size = 24
    for i in range(num_rivers):
        logging.info(str(i) + '/' + str(num_rivers) + ': Started ' + datetime.datetime.utcnow().strftime("%D at %R"))

        min_arr = []
        mean_arr = []
        max_arr = []

        # on the sample outputs the dimensions are time, rivid
        arr = source_nc.variables['Qout'][:, i]
        # on the rapid docker image, the dimensions are rivid, time, i think
        # arr = source_nc.variables['Qout'][i, :]

        # if the array is at least 'size' long
        while len(arr) >= size:
            # take the first 'size' pieces
            piece = arr[:size]
            # get the min, mean, max and put them into a list
            min_arr.append(min(piece))
            mean_arr.append(statistics.mean(piece))
            max_arr.append(max(piece))
            # drop the first 'size' elements in the array
            arr = arr[size:]
        # if it doesn't divide perfectly in 'size' len pieces, alert you
        if len(arr) > 0:
            logging.info('Did not divide evenly')
            logging.info(len(arr))
            logging.info(arr)

        # write the new arrays to the new variables
        logging.info('  writing Qmin variables')
        new_nc.variables['Qout_min'][:, i] = min_arr
        logging.info('  writing Qmean variables')
        new_nc.variables['Qout_mean'][:, i] = mean_arr
        logging.info('  writing Qmax variables')
        new_nc.variables['Qout_max'][:, i] = max_arr
        new_nc.sync()
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
    # logging.basicConfig(filename='/Users/rileyhales/Downloads/era5samplefiles/log.log', filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('ERA5 aggregation started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    aggregate_by_day(sys.argv[1])
    # aggregate_by_day('/Users/rileyhales/Downloads/era5samplefiles/nam_clearwater/Qout_era5_t640_1hr_19790101to20181231.nc')
