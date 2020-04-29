import os
import sys
import netCDF4
import logging
import statistics
import math
import datetime
import pandas


def solve_gumbel_flow(std, xbar, rp):
    """
    Solves the Gumbel Type I pdf = exp(-exp(-b))
    where b is the covariate
    """
    # xbar = statistics.mean(year_max_flow_list)
    # std = statistics.stdev(year_max_flow_list, xbar=xbar)
    return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)


def daily_to_yearly_max_flow(daily_flow_list, start_yr, end_yr):
    yearly_max_flows = []
    dates = pandas.Series(pandas.date_range(str(start_yr) + '-1-1 00:00:00', periods=len(daily_flow_list), freq='D'))
    df = pandas.DataFrame(daily_flow_list, columns=['simulated_flow'], index=dates)
    for i in range(start_yr, end_yr + 1):
        yearly_max_flows.append(max(df[df.index.year == i]['simulated_flow']))
    return yearly_max_flows


def gumbel_return_periods(path_Qout):
    # sort out the file paths
    if not os.path.isfile(path_Qout):
        logging.info(path_Qout)
        raise FileNotFoundError('Qout file not found at this path')

    flow_var = 'Qout'
    if 'erai' in str(os.path.basename(path_Qout)).lower():
        start_yr = 1980
        end_yr = 2014
        # series_len = 12784
    elif 'era5' in str(os.path.basename(path_Qout)).lower():
        start_yr = 1979
        end_yr = 2018
        # series_len = 350616
    else:
        raise ValueError('unrecognized file, should be erai or era5')

    rp_nc_path = os.path.join(os.path.dirname(path_Qout), 'Gumbel_return_periods.nc4')

    # read the netcdfs
    source_nc = netCDF4.Dataset(filename=path_Qout, mode='r')
    rp_nc = netCDF4.Dataset(filename=rp_nc_path, mode='w')

    # create rivid and time dimensions
    logging.info('creating new netcdf variables/dimensions')
    rp_nc.createDimension('rivid', size=source_nc.dimensions['rivid'].size)
    rp_nc.createDimension('lat', size=source_nc.dimensions['lat'].size)
    rp_nc.createDimension('lon', size=source_nc.dimensions['lon'].size)
    # create rivid and time variables
    rp_nc.createVariable('rivid', datatype='f4', dimensions=('rivid',))
    # create lat and lon variables
    rp_nc.createVariable('lat', datatype='f4', dimensions=('rivid',))
    # create the variables for the flows
    rp_nc.createVariable('return_period_100', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('return_period_50', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('return_period_25', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('return_period_10', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('return_period_5', datatype='f4', dimensions=('rivid',))
    rp_nc.createVariable('return_period_2', datatype='f4', dimensions=('rivid',))

    # determine which order of dimensions
    if source_nc.variables[flow_var].dimensions == ('time', 'rivid'):
        time_first = True
    elif source_nc.variables[flow_var].dimensions == ('rivid', 'time'):
        time_first = False
    else:
        logging.info('Unable to identify the order of the Qout variables\' dimensions. Exiting')
        exit()

    # configure the rivid variable
    logging.info('populating the rivid variable')
    rp_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]

    # for each river read the whole time series
    num_rivers = source_nc.dimensions['rivid'].size

    for i in range(num_rivers):
        logging.info(str(i) + '/' + str(num_rivers))

        # slice the array propertly based on the order of the dimensions
        if time_first:
            yearly_max_flows = daily_to_yearly_max_flow(source_nc.variables[flow_var][:, i], start_yr, end_yr)
        else:
            yearly_max_flows = daily_to_yearly_max_flow(source_nc.variables[flow_var][i, :], start_yr, end_yr)

        xbar = statistics.mean(yearly_max_flows)
        std = statistics.stdev(yearly_max_flows, xbar=xbar)
        rp_nc.variables['return_period_100'][i] = solve_gumbel_flow(std, xbar, 100)
        rp_nc.variables['return_period_50'][i] = solve_gumbel_flow(std, xbar, 50)
        rp_nc.variables['return_period_25'][i] = solve_gumbel_flow(std, xbar, 25)
        rp_nc.variables['return_period_10'][i] = solve_gumbel_flow(std, xbar, 10)
        rp_nc.variables['return_period_5'][i] = solve_gumbel_flow(std, xbar, 5)
        rp_nc.variables['return_period_2'][i] = solve_gumbel_flow(std, xbar, 2)
        rp_nc.sync()

    source_nc.close()
    logging.info('')
    logging.info('FINISHED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))
    return


# for running this script from the command line with a script
if __name__ == '__main__':
    """
    sys.argv[0] this script e.g. generate_gumbel_return_periods.py
    sys.argv[1] path to Qout file
    sys.argv[2] path to directory for storing logs
    """
    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(
        filename=os.path.join(sys.argv[2], os.path.basename(os.path.dirname(sys.argv[1])) + '.log'),
        filemode='w',
        level=logging.INFO,
        format='%(message)s'
    )
    logging.info('Gumbel Return Period Processing started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    gumbel_return_periods(sys.argv[1])
