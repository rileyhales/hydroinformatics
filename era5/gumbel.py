import os
import sys
import netCDF4
import logging
import statistics
import math
import datetime


def solve_gumbel_flow(std, xbar, rp):
    """
    Solves the Gumbel Type I pdf = exp(-exp(-b))
    where b is the covariate
    """
    # xbar = statistics.mean(year_max_flow_list)
    # std = statistics.stdev(year_max_flow_list, xbar=xbar)
    return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)


def daily_to_yearly_max_flow(daily_flow_list):
    yearly_max_flows = []
    return yearly_max_flows


def gumbel_return_periods(path_Qout):
    # sort out the file paths
    if not os.path.isfile(path_Qout):
        raise FileNotFoundError('Qout file not found at this path')
    rp_nc_path = os.path.join(os.path.dirname(path_Qout), 'return_periods.nc4')

    # read the netcdfs
    source_nc = netCDF4.Dataset(filename=path_Qout, mode='r')
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
        logging.info(str(i) + '/' + str(num_rivers) + '. Started ' + datetime.datetime.utcnow().strftime("%D at %R"))
        yearly_max_flows = daily_to_yearly_max_flow(source_nc.variables['Qout'][:, i])
        xbar = statistics.mean(yearly_max_flows)
        std = statistics.stdev(yearly_max_flows, xbar=xbar)
        rp_nc.variables['r100'][i] = solve_gumbel_flow(std, xbar, 100)
        rp_nc.variables['r50'][i] = solve_gumbel_flow(std, xbar, 50)
        rp_nc.variables['r25'][i] = solve_gumbel_flow(std, xbar, 25)
        rp_nc.variables['r20'][i] = solve_gumbel_flow(std, xbar, 20)
        rp_nc.variables['r10'][i] = solve_gumbel_flow(std, xbar, 10)
        rp_nc.variables['r2'][i] = solve_gumbel_flow(std, xbar, 2)
        rp_nc.sync()

    logging.info('')
    logging.info('FINISHED')
    logging.info(datetime.datetime.utcnow().strftime("%D at %R"))
    return


# for running this script from the command line with a script
if __name__ == '__main__':
    # sys.argv[0] this script e.g. gumbel.py
    # sys.argv[1] path to Qout file
    # sys.argv[2] path to log file

    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=sys.argv[2], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('Gumbel Return Period Processing started on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    gumbel_return_periods(sys.argv[1])