import os
import netCDF4 as nc
import pandas as pd


def make_return_period_flow_summary(qout_file, rp_file, csv_save_dir):
    """
    Creates a csv file with the columns:
        comid, stream_lat, stream_lon, return_period_exceeded, flow
    For example:
        10000, 40, -30, 25, 150
    indicates that comid 10000, located at lat 40 and lon -30, surpassed it's 25 year return period flow with a flow of
    150 cubic meters per second.

    Args:
        qout_file: the full path to a Qout file produced by the ECMWF rapid workflow
        rp_file: the full path to the Gumbel return periods file for the same region
    """
    # get the comids in qout file
    qout_data = nc.Dataset(qout_file, 'r')
    comids_qout = qout_data['rivid'][:]

    return_period_nc = nc.Dataset(rp_file, 'r')
    comids_rp = list(return_period_nc.variables['rivid'][:])
    # r100_thresholds = return_period_nc.variables['return_period_100'][:]
    # r50_thresholds = return_period_nc.variables['return_period_50'][:]
    # r25_thresholds = return_period_nc.variables['return_period_25'][:]
    r20_thresholds = return_period_nc.variables['return_period_20'][:]
    r10_thresholds = return_period_nc.variables['return_period_10'][:]
    r2_thresholds = return_period_nc.variables['return_period_2'][:]
    lat = return_period_nc.variables['lat'][:]
    lon = return_period_nc.variables['lon'][:]
    return_period_nc.close()

    largeflows = pd.DataFrame(columns=['comid', 'stream_lat', 'stream_lon', 'return_period', 'flow'])

    for index_qout, comid in enumerate(comids_qout):
        index_rp = comids_rp.index(comid)
        maxflow = max(qout_data['Qout'][index_rp])

        # if maxflow >= r100_thresholds[index_rp]:
        #     rp = 100
        # elif maxflow >= r50_thresholds[index_rp]:
        #     rp = 50
        # elif maxflow >= r25_thresholds[index_rp]:
        #     rp = 25
        if maxflow >= r20_thresholds[index_rp]:
            rp = 20
        elif maxflow >= r10_thresholds[index_rp]:
            rp = 10
        elif maxflow >= r2_thresholds[index_rp]:
            rp = 2
        else:
            continue
        largeflows = largeflows.append({
            'comid': int(comid),
            'stream_lat': lat[index_rp],
            'stream_lon': lon[index_rp],
            'return_period': rp,
            'flow': maxflow,
        }, ignore_index=True)

    largeflows.to_csv(os.path.join(csv_save_dir, 'forecasted_return_periods_summary.csv'))
    return

make_return_period_flow_summary(
    '/Users/rileyhales/Downloads/tmp/Qout_islands_geoglows_52.nc',
    '/Users/rileyhales/Downloads/tmp/return_periods_erai_t511_24hr_19800101to20141231.nc',
    '/Users/rileyhales/Downloads/tmp/'
)