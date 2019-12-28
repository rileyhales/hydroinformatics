import netCDF4
import os


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
        print('Did not divide evenly')
        print(len(arr))
        print(arr)
    # return the stats about the segmented arrays
    return min_arrs, mean_arrs, max_arrs


def aggregate(path_Qout, agg_hours=24):
    # make the file paths
    if not os.path.isfile(path_Qout):
        raise FileNotFoundError('Qout file not found at this path')

    # open the netcdf, create new variables
    nc = netCDF4.Dataset(filename=path_Qout, mode='r+')
    nc.createVariable('Qout_min', datatype='f4', dimensions=('time', 'rivid'))
    nc.createVariable('Qout_mean', datatype='f4', dimensions=('time', 'rivid'))
    nc.createVariable('Qout_max', datatype='f4', dimensions=('time', 'rivid'))

    for i in range(nc.dimensions['rivid'].size):
        print(i)
        tmp = nc.variables['Qout'][:, i]
        min_arrs = []
        mean_arrs = []
        max_arrs = []
        # if the array is at least 'size' long
        while len(tmp) >= agg_hours:
            # take the first 'size' pieces
            piece = tmp[:agg_hours]
            # get the min, mean, max and put them into a list
            min_arrs.append(min(piece))
            mean_arrs.append(sum(piece) / agg_hours)
            max_arrs.append(max(piece))
            # drop the first 'size' elements in the array
            tmp = tmp[agg_hours:]
            print(tmp.size)
        # if it doesn't divide perfectly in 'size' len pieces, alert you
        if len(tmp) > 0:
            print('Did not divide evenly')
            print(len(tmp))
            print(tmp)
        # write the new arrays to the new variables
        nc.variables['Qout_min'][:, i] = min_arrs
        nc.variables['Qout_mean'][:, i] = mean_arrs
        nc.variables['Qout_max'][:, i] = max_arrs
    return


path_Qout = '/Users/rileyhales/era5sampledata/sampledata/nam_clearwater/Qout_era5_t640_1hr_19790101to20181231.nc'

aggregate(path_Qout, agg_hours=24)
