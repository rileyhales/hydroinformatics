import netCDF4
import os
import logging
import datetime
import multiprocessing


def generate_new_nc(path_to_source_nc, path_to_new_nc):
    # read the netcdfs
    source_nc = netCDF4.Dataset(filename=path_to_source_nc, mode='r')
    new_nc = netCDF4.Dataset(filename=path_to_new_nc, mode='w')

    # create rivid and time dimensions
    logging.info('creating new netcdf variables/dimensions')
    new_nc.createDimension('rivid', size=source_nc.dimensions['rivid'].size)
    new_nc.createDimension('time', size=source_nc.dimensions['time'].size // 24)
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
    logging.info('populating the rivid variable')
    new_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]

    logging.info('new nc created')
    logging.info('')
    return source_nc.dimensions['rivid'].size


def aggregate_rivers(river_number):
    path_to_new_nc = '/Users/rileyhales/Downloads/era5samplefiles/temporary/'

    agg_hours = 24
    logging.info(str(river_number) + '. Started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    tmp = source_nc.variables['Qout'][:, river_number]
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
        logging.info('      Did not divide evenly')
        logging.info(len(tmp))
        logging.info(tmp)
    # write the new arrays to the new variables
    logging.info('  writing Qout variables')

    new_nc = netCDF4.Dataset(filename=path_to_new_nc + river_number + '.nc4', mode='w')
    new_nc.createDimension('time', size=1)
    # create rivid and time variables
    new_nc.createVariable('time', datatype='f4', dimensions=('time',), )
    # create the variables for the flows
    new_nc.createVariable('Qout_min', datatype='f4', dimensions=('time',))
    new_nc.createVariable('Qout_mean', datatype='f4', dimensions=('time',))
    new_nc.createVariable('Qout_max', datatype='f4', dimensions=('time',))

    new_nc.variables['Qout_min'][:] = min_arrs
    new_nc.variables['Qout_mean'][:] = mean_arrs
    new_nc.variables['Qout_max'][:] = max_arrs
    logging.info('  finished river ' + str(river_number))


path_to_log = '/Users/rileyhales/Downloads/era5samplefiles/test.log'
path_to_source_nc = '/Users/rileyhales/Downloads/era5samplefiles/nam_clearwater/Qout_era5_t640_1hr_19790101to20181231.nc'

logging.basicConfig(filename=path_to_log, filemode='w', level=logging.INFO, format='%(message)s')
logging.info('ERA5 aggregation started on ' + datetime.datetime.utcnow().strftime("%D at %R"))

path_to_new_nc = '/Users/rileyhales/Downloads/era5samplefiles/nam_clearwater/Aggregated_Qout.nc4'
number_of_rivers = generate_new_nc(path_to_source_nc, path_to_new_nc)

pool = multiprocessing.Pool()
pool.map(aggregate_rivers, range(number_of_rivers))
