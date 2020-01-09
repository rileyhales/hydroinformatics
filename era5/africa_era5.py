import netCDF4
import os
import datetime
import logging


# the function that actually subdivides the array
def subset_list(arr, size):
    min_arrs = []
    mean_arrs = []
    max_arrs = []
    # if the array is at least 'size' long
    while len(arr) >= size:
        # take the first 'size' pieces
        piece = arr[:size]
        # get the min, mean, max and put them into a list
        min_arrs.append(min(piece))
        mean_arrs.append(sum(piece)/size)
        max_arrs.append(max(piece))
        # drop the first 'size' elements in the array
        arr = arr[size:]
    # if it doesn't divide perfectly in 'size' len pieces, alert you
    if len(arr) > 0:
        logging.info('Did not divide evenly')
        logging.info(len(arr))
        logging.info(arr)
    # return the stats about the segmented arrays
    return min_arrs, mean_arrs, max_arrs


def aggregate_by_day(path_Qout):
    agg_hours = 24

    # sort out the file paths
    if not os.path.isfile(path_Qout):
        raise FileNotFoundError('Qout file not found at this path')

    # read the netcdfs
    source_nc = netCDF4.Dataset(filename=path_Qout, mode='r')
    new_nc = netCDF4.Dataset(filename=os.path.join(os.path.dirname(path_Qout), 'Aggregated_Qout.nc4'), mode='w')

    logging.info('creating new netcdf variables/dimensions')
    # create rivid and time dimensions
    new_nc.createDimension('rivid', size=source_nc.dimensions['rivid'].size)
    # new_nc.createDimension('time', size=source_nc.dimensions['time'].size // 24)
    new_nc.createDimension('time', size=4446)

    # create rivid and time variables
    new_nc.createVariable('rivid', datatype='f4', dimensions=('rivid',), )
    new_nc.createVariable('time', datatype='f4', dimensions=('time',), )

    # create the variables for the flows
    new_nc.createVariable('Qout_min', datatype='f4', dimensions=('time', 'rivid'))
    new_nc.createVariable('Qout_mean', datatype='f4', dimensions=('time', 'rivid'))
    new_nc.createVariable('Qout_max', datatype='f4', dimensions=('time', 'rivid'))

    # configure the time variable
    new_nc.variables['time'][:] = range(new_nc.dimensions['time'].size)
    new_nc.variables['time'].__dict__['units'] = 'days since 1979-01-01 00:00:00+00:00'
    new_nc.variables['time'].__dict__['calendar'] = 'gregorian'

    # configure the rivid variable
    new_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]

    # for each river read the whole time series
    num_rivers = source_nc.dimensions['rivid'].size
    for i in range(num_rivers):
        logging.info('***' + str(i) + '/' + str(num_rivers) + '. Started ' + datetime.datetime.utcnow().strftime("%D at %R"))
        tmp = source_nc.variables['Qout'][:, i]
        # size should be 14610*24=350640
        # logging.info(tmp.size)
        min_arrs = []
        mean_arrs = []
        max_arrs = []
        # if the array is at least 24 steps long
        while len(tmp) >= agg_hours:
            # take the first 24 pieces
            piece = tmp[:agg_hours]
            # get the min, mean, max and put them into a list
            min_arrs.append(min(piece))
            mean_arrs.append(sum(piece) / agg_hours)
            max_arrs.append(max(piece))
            # drop the first 24 steps
            tmp = tmp[agg_hours:]
        # if it didn't divide perfectly into 24 hour segments, say something
        if len(tmp) > 0:
            logging.info('Did not divide evenly')
            # logging.info(len(tmp))
            # logging.info(tmp)
        # write the new arrays to the new variables
        logging.info('   writing qmin')
        new_nc.variables['Qout_min'][:, i] = min_arrs
        logging.info('   writing qmean')
        new_nc.variables['Qout_mean'][:, i] = mean_arrs
        logging.info('   writing qmax')
        new_nc.variables['Qout_max'][:, i] = max_arrs
    return


# for running this script from the command line with a script
logging.info('ERA5 aggregation started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
aggregate_by_day('sampledata/africa-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc')
