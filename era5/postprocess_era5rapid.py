import datetime
import logging
import math
import os
import statistics
import sys

import netCDF4
import pandas


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
    logging.info('Daily aggregated data saved to ' + newfilepath)
    logging.info('FINISHED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))
    return newfilepath


def solve_gumbel_flow(std, xbar, rp):
    """
    Solves the Gumbel Type I pdf = exp(-exp(-b))
    where b is the covariate
    """
    # xbar = statistics.mean(year_max_flow_list)
    # std = statistics.stdev(year_max_flow_list, xbar=xbar)
    return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)


def daily_to_yearly_max_flow(daily_flow_list):
    # the order of the flows doesn't matter so we can return it as a list even though thats mutable
    yearly_max_flows = []
    dates = pandas.Series(pandas.date_range('1979-1-1 00:00:00', periods=len(daily_flow_list), freq='D'))
    df = pandas.DataFrame(daily_flow_list, columns=['simulated_flow'], index=dates)
    for i in range(1979, 2019):
        yearly_max_flows.append(max(df[df.index.year == i]['simulated_flow']))
    return yearly_max_flows


def gumbel_return_periods(path_dayagg):
    # sort out the file paths
    if not os.path.isfile(path_dayagg):
        raise FileNotFoundError('Qout file not found at this path')
    rp_nc_path = os.path.join(os.path.dirname(path_dayagg), 'Gumbel_return_periods.nc4')

    # read the netcdfs
    source_nc = netCDF4.Dataset(filename=path_dayagg, mode='r')
    rp_nc = netCDF4.Dataset(filename=rp_nc_path, mode='w')

    # create rivid and time dimensions
    logging.info('creating new netcdf variables/dimensions')
    rp_nc.createDimension('rivid', size=source_nc.dimensions['rivid'].size)
    # create rivid and time variables
    rp_nc.createVariable('rivid', datatype='f4', dimensions=('rivid',))
    # create the variables for the flows
    rp_nc.createVariable('r100', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('r50', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('r25', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('r20', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('r10', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('r2', datatype='f4', dimensions=('rivid',))

    # configure the rivid variable
    logging.info('populating the rivid variable')
    rp_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]

    # for each river read the whole time series
    num_rivers = source_nc.dimensions['rivid'].size
    for i in range(num_rivers):
        logging.info(str(i) + '/' + str(num_rivers) + ': Started ' + datetime.datetime.utcnow().strftime("%D at %R"))
        yearly_max_flows = daily_to_yearly_max_flow(source_nc.variables['Qout_max'][:, i])
        xbar = statistics.mean(yearly_max_flows)
        std = statistics.stdev(yearly_max_flows, xbar=xbar)
        rp_nc.variables['r100'][i] = solve_gumbel_flow(std, xbar, 100)
        rp_nc.variables['r50'][i] = solve_gumbel_flow(std, xbar, 50)
        rp_nc.variables['r25'][i] = solve_gumbel_flow(std, xbar, 25)
        rp_nc.variables['r20'][i] = solve_gumbel_flow(std, xbar, 20)
        rp_nc.variables['r10'][i] = solve_gumbel_flow(std, xbar, 10)
        rp_nc.variables['r2'][i] = solve_gumbel_flow(std, xbar, 2)
        rp_nc.sync()

    rp_nc.close()
    source_nc.close()
    logging.info('')
    logging.info('FINISHED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))
    return rp_nc_path


# for running this script from the command line with a script
if __name__ == '__main__':
    """
    sys.argv[0] this script e.g. postprocess_era5rapid.py
    sys.argv[1] path to era5 rapid Qout file
    sys.argv[2] (OPTIONAL) path to log file
    """
    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=sys.argv[2], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('ERA5 aggregation started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    path_dayagg = aggregate_by_day(sys.argv[1])
    logging.info('')
    logging.info('Gumbel Return Period Processing started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    gumbel_return_periods(path_dayagg)
    logging.info('')
    logging.info('ALL POSTPROCESSING COMPLETED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))

