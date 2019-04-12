def nc1_to_gtiff(file_path, var, save_dir_path):
    """
    Description: This script accepts a netcdf file in a geographic coordinate system, specifically the NASA GLDAS
        netcdfs, and extracts the data from one variable and the lat/lon steps to create a geotiff of that information.
    Dependencies: netCDF4, numpy, gdal, osr
    Params: View README.md
    Returns: Creates a geotiff named 'geotiff.tif' in the directory specified
    Author: Riley Hales, RCH Engineering, March 2019
    """
    import netCDF4
    import numpy
    import gdal
    import osr

    # Reading in data from the netcdf
    nc_obj = netCDF4.Dataset(file_path, 'r')
    var_data = nc_obj.variables[var][:]
    lat = nc_obj.variables['lat'][:]
    lon = nc_obj.variables['lon'][:]

    # format the array of information going to the tiff
    array = numpy.asarray(var_data)[0, :, :]
    array[array < -9000] = numpy.nan                # change the comparator to git rid of the fill value
    array = array[::-1]       # vertically flip array so the orientation is right (you just have to, try it)

    # Creates geotiff raster file (filepath, x-dimensions, y-dimensions, number of bands, datatype)
    gtiffdriver = gdal.GetDriverByName('GTiff')
    new_gtiff = gtiffdriver.Create(save_dir_path + 'geotiff.tif', len(lon), len(lat), 1, gdal.GDT_Float32)

    # geotransform (sets coordinates) = (x-origin(left), x-width, x-rotation, y-origin(top), y-rotation, y-width)
    yorigin = lat.max()
    xorigin = lon.min()
    xres = lat[1] - lat[0]
    yres = lon[1] - lon[0]
    new_gtiff.SetGeoTransform((xorigin, xres, 0, yorigin, 0, -yres))

    # Set the projection of the geotiff (Projection EPSG:4326, Geographic Coordinate System WGS 1984 (degrees lat/lon)
    new_gtiff.SetProjection(osr.SRS_WKT_WGS84)

    # actually write the data array to the tiff file and save it
    new_gtiff.GetRasterBand(1).WriteArray(array)      # write band to the raster (variable array)
    new_gtiff.FlushCache()                            # write to disk

    return


def ncAll_to_gtiff():
    """
    Description: This script accepts a netcdf file in a geographic coordinate system, specifically the NASA GLDAS
        netcdfs, and extracts the data from all variables in the file and the lat/lon steps to create a geotiff of that
        information.
    Dependencies: netCDF4, numpy, gdal, osr
    Params: View README.md
    Returns: Creates a geotiff named 'geotiff.tif' in the directory specified
    Author: Riley Hales, RCH Engineering, March 2019
    """
    return


def ncDir_to_MBgtiff(dir_path, var, save_dir_path):
    """
    Description: This script accepts a directory of time seperated netcdf files in a geographic coordinate system,
        specifically the NASA GLDAS netcdfs, and extracts the data for one variable from all timesteps and sets the
        bounding information and projection for the geotiff.
    Dependencies: os, netCDF4, numpy, gdal, osr
    Params: View README.md
    Returns: Creates a geotiff named 'geotiff.tif' in the directory specified
    Author: Riley Hales, RCH Engineering, March 2019
    """
    import os
    import netCDF4
    import numpy
    import gdal
    import osr

    # get a list of all the netcdf files
    listfiles = os.listdir(dir_path)
    listfiles.sort()
    if listfiles[0] == '.DS_Store':
        listfiles.remove(listfiles[0])

    # Get data from one netcdf to set geotiff attributes
    file_path = os.path.join(dir_path, listfiles[0])
    nc_obj = netCDF4.Dataset(file_path, 'r')
    lat = nc_obj.variables['lat'][:]
    lon = nc_obj.variables['lon'][:]

    # Creates geotiff raster file (filepath, x-dimensions, y-dimensions, number of bands, datatype)
    gtiffdriver = gdal.GetDriverByName('GTiff')
    new_gtiff = gtiffdriver.Create(save_dir_path + 'geotiff.tif', len(lon), len(lat), len(listfiles), gdal.GDT_Float32)

    # geotransform (sets coordinates) = (x-origin(left), x-width, x-rotation, y-origin(top), y-rotation, y-width)
    yorigin = lat.max()
    xorigin = lon.min()
    xres = (lat.max() - lat.min()) / len(lat)
    yres = (lon.max() - lon.min()) / len(lon)
    new_gtiff.SetGeoTransform((xorigin, xres, 0, yorigin, 0, -yres))

    # Set the projection of the geotiff (Projection EPSG:4326, Geographic Coordinate System WGS 1984 (degrees lat/lon)
    new_gtiff.SetProjection(osr.SRS_WKT_WGS84)

    # write each timestep's data to the geotiff in a separate band
    for i in range(len(listfiles)):
        file_path = os.path.join(dir_path, listfiles[i])
        nc_obj = netCDF4.Dataset(file_path, 'r')
        var_data = nc_obj.variables[var][:]
        lat = nc_obj.variables['lat'][:]
        lon = nc_obj.variables['lon'][:]
        # format the array of information going to the tiff
        array = numpy.asarray(var_data)[:, :]
        array[array < -9000] = numpy.nan                # change the comparator to git rid of the fill value
        array = array[::-1]             # flip the array so the orientation is right (you just have to, try it without)
        # actually write the data array to the tiff file and save it
        new_gtiff.GetRasterBand(i + 1).WriteArray(array)      # write band to the raster (variable array)

    new_gtiff.FlushCache()                            # write to disk

    return


# nc1_to_geotiff(r'/Users/rileyhales/Documents/sampledata/n41w112_30m/GLDAS_NOAH025_M.A201902.021.nc4', 'Tair_f_inst', r'/Users/rileyhales/Documents/nctools/')
# ncAll_to_gtiff()
# ncDir_to_MBgtiff(r'/Users/rileyhales/thredds/malaria', 'Tair_f_tavg', r'/Users/rileyhales/scratchworkspace/')
