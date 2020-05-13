import netCDF4 as nc
import pandas as pd
import os
import numpy as np
import plotly.graph_objs as go


def gen_simulated_averages(path_Qout, write_frequency=1000):
    # sort out the file paths
    if not os.path.isfile(path_Qout):
        raise FileNotFoundError('Qout file not found at this path')

    newfilepath = os.path.join(os.path.dirname(path_Qout), 'simulated_average_flows.nc4')

    # read the source netcdf
    source_nc = nc.Dataset(filename=path_Qout, mode='r')

    # create the new netcdf
    new_nc = nc.Dataset(filename=newfilepath, mode='w')
    # create rivid and time *dimensions*
    new_nc.createDimension('rivid', size=source_nc.dimensions['rivid'].size)
    new_nc.createDimension('day_of_year', size=365)
    new_nc.createDimension('month', size=12)
    # create rivid and time *variables*
    new_nc.createVariable('rivid', datatype='i4', dimensions=('rivid',))
    new_nc.createVariable('day_of_year', datatype='i4', dimensions=('day_of_year',))
    new_nc.createVariable('month', datatype='i4', dimensions=('month',))
    # fill those variables with their data
    new_nc.variables['rivid'][:] = source_nc.variables['rivid'][:]
    new_nc.variables['day_of_year'][:] = list(range(1, 366))
    new_nc.variables['month'][:] = list(range(1, 13))
    # create the variables for the flows
    new_nc.createVariable('daily_min', datatype='f4', dimensions=('rivid', 'day_of_year'))
    new_nc.createVariable('daily_avg', datatype='f4', dimensions=('rivid', 'day_of_year'))
    new_nc.createVariable('daily_max', datatype='f4', dimensions=('rivid', 'day_of_year'))
    new_nc.createVariable('monthly_min', datatype='f4', dimensions=('rivid', 'month'))
    new_nc.createVariable('monthly_avg', datatype='f4', dimensions=('rivid', 'month'))
    new_nc.createVariable('monthly_max', datatype='f4', dimensions=('rivid', 'month'))

    # collect information used to create iteration parameters
    num_rivers = source_nc.dimensions['rivid'].size

    # create a set of indices for slicing the array in sub groups determined by the write_frequency param
    indices = list(range(num_rivers))
    index_pairs = []
    while len(indices) > 0:
        arr = indices[:write_frequency]
        index_pairs.append((arr[0], arr[-1]))
        indices = indices[write_frequency:]

    # create a list of times for the dataframe
    times = pd.to_datetime(source_nc['time'][:], origin='unix', unit='s', utc=True)

    for group_num, pairs in enumerate(index_pairs):
        start_idx = pairs[0]
        end_idx = pairs[1]

        # depending on the version of rapid used, the dimension order is different
        if source_nc.variables['Qout'].dimensions == ('time', 'rivid'):
            arr = np.asarray(source_nc.variables['Qout'][:, start_idx:end_idx])
        elif source_nc.variables['Qout'].dimensions == ('rivid', 'time'):
            arr = np.transpose(np.asarray(source_nc.variables['Qout'][start_idx:end_idx, :]))

        columns = source_nc['rivid'][start_idx:end_idx]

        # made a dataframe of that array of flows where the index is the day of the year ('%j')
        df = pd.DataFrame(arr, index=times.strftime('%j'), columns=columns)
        # for each day of the year
        for i in range(1, 366):
            # filter the data frame
            day_of_year_flows = df[df.index == f'{i:03}']
            # select min/avg/max flow by column and store it in the new netcdf's variable
            # use i in the range to select the day of the year but store at i-1 because indexes start at 0, not 1
            new_nc['daily_min'][start_idx:end_idx, i - 1] = day_of_year_flows.min(axis=0).to_numpy()
            new_nc['daily_avg'][start_idx:end_idx, i - 1] = day_of_year_flows.mean(axis=0).to_numpy()
            new_nc['daily_max'][start_idx:end_idx, i - 1] = day_of_year_flows.max(axis=0).to_numpy()
        # write the changes to the file on the hard drive
        new_nc.sync()

        # now redo the dataframe with the months and repeat the process
        df = pd.DataFrame(arr, index=times.strftime('%m'), columns=columns)
        # for each month of the year
        for i in range(1, 13):
            # filter the data frame
            month_of_year_flows = df[df.index == f'{i:02}']
            # select min/avg/max flow by column and store it in the new netcdf's variable
            # use i in the range to select the day of the year but store at i-1 because indexes start at 0, not 1
            new_nc['monthly_min'][start_idx:end_idx, i - 1] = month_of_year_flows.min(axis=0).to_numpy()
            new_nc['monthly_avg'][start_idx:end_idx, i - 1] = month_of_year_flows.mean(axis=0).to_numpy()
            new_nc['monthly_max'][start_idx:end_idx, i - 1] = month_of_year_flows.max(axis=0).to_numpy()
        # write the changes to the file on the hard drive
        new_nc.sync()

    # close the new netcdf
    new_nc.close()
    source_nc.close()

    return newfilepath


def compare_with_plots(new_averages_file, old_averages_file, rivid):
    newnc = nc.Dataset(new_averages_file, 'r')
    idx = list(newnc.variables['rivid'][:]).index(rivid)
    day_min = newnc['daily_min'][idx, :]
    day_avg = newnc['daily_avg'][idx, :]
    day_max = newnc['daily_max'][idx, :]
    month_min = newnc['monthly_min'][idx, :]
    month_avg = newnc['monthly_avg'][idx, :]
    month_max = newnc['monthly_max'][idx, :]
    newnc.close()
    oldnc = nc.Dataset(old_averages_file)
    idx = list(oldnc.variables['rivid'][:]).index(rivid)
    old_day_min = oldnc.variables['min_flow'][idx, :]
    old_day_avg = oldnc.variables['average_flow'][idx, :]
    old_day_max = oldnc.variables['max_flow'][idx, :]
    oldnc.close()
    days = list(range(1, 366))
    scatters = [
        go.Scatter(
            name='Old Min',
            x=days,
            y=old_day_min,
        ),
        go.Scatter(
            name='New Min',
            x=days,
            y=day_min,
        ),
        go.Scatter(
            name='Old Avg',
            x=days,
            y=old_day_avg,
        ),
        go.Scatter(
            name='New Avg',
            x=days,
            y=day_avg,
        ),
        go.Scatter(
            name='Old Max',
            x=days,
            y=old_day_max,
        ),
        go.Scatter(
            name='New Max',
            x=days,
            y=day_max,
        ),
    ]
    go.Figure(scatters).show()
    go.Figure([
        go.Scatter(
            name='Monthly Min',
            x=list(range(1, 13)),
            y=month_min
        ),
        go.Scatter(
            name='Monthly Avg',
            x=list(range(1, 13)),
            y=month_avg
        ),
        go.Scatter(
            name='Monthly Max',
            x=list(range(1, 13)),
            y=month_max
        ),
    ]).show()
    return


if __name__ == '__main__':
    historical_sim_rapid_output = '/Users/riley/code/gsp_rest_api/output/era-5/japan-geoglows/Qout_era5_t640_24hr_19790101to20181231.nc'
    gen_simulated_averages(historical_sim_rapid_output, 1000)

    # verify
    # new_averages_file = '/Users/riley/code/gsp_rest_api/output/era-5/japan-geoglows/simulated_average_flows.nc4'
    # old_averages_file = '/Users/riley/code/gsp_rest_api/output/era-5/japan-geoglows/seasonal_averages_era5_t640_24hr_19790101to20181231.nc'
    # rivid = 3001070
    # compare_with_plots(new_averages_file, old_averages_file, rivid)
