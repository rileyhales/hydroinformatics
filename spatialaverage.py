def nc_to_geotiff(file_path, var, save_dir_path):
    """
    This script accepts a netcdf file in a geographic coordinate system, specifically the NASA GLDAS netcdfs, and
    extracts the data from one variable and the lat/lon steps to create a geotiff of that information
    """
    import netCDF4
    import numpy
    import gdal
    import osr

    # Reading in data from the netcdf
    nc_obj = netCDF4.Dataset(file_path, 'r')
    var_data = nc_obj.variables[var][:]
    print(var_data)
    lat = nc_obj.variables['lat'][:]
    print(lat)
    lon = nc_obj.variables['lon'][:]
    print(lon)

    # Create the array with the variable information at the size of
    x = numpy.zeros((len(lat), len(lon)), float)
    x[:, :] = var_data[:]
    print(x)

    # calculate the geographic transform information
    lon_steps = len(lon)
    lat_steps = len(lat)
    xmin = lon.min()
    xmax = lon.max()
    ymin = lat.min()
    ymax = lat.max()
    xres = (xmax - xmin) / float(lon_steps)
    yres = (ymax - ymin) / float(lat_steps)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)

    # Creates geotiff raster file
    new_geotiff = gdal.GetDriverByName('GTiff').Create(save_dir_path + 'geotiff.tif', lat_steps, lon_steps, 1, gdal.GDT_Float32)

    new_geotiff.SetGeoTransform(geotransform)                # specify coords
    srs = osr.SpatialReference().ImportFromEPSG(3857)        # establish encoding WGS84 lat/long
    new_geotiff.SetProjection(srs.ExportToWkt())             # export coords to file
    new_geotiff.GetRasterBand(1).WriteArray(x)               # write band to the raster (variable array)
    new_geotiff.FlushCache()                                 # write to disk

    return


def spatialaverage(rasterpath, shape_path):
    """
    Spatial average returns the arithmetic mean of the values in a netcdf raster within the boundaries of a shapefile
    """
    import fiona
    import rasterio
    from rasterio.mask import mask
    from rasterio.plot import show
    import numpy

    # read the raster into a rasterio object
    raster_obj = rasterio.open(rasterpath)
    rasterio.plot.show(raster_obj)

    # read the shapefile information into a fiona object
    shp_object = fiona.open(shape_path, 'r')
    shp_geometry = [feature["geometry"] for feature in shp_object]

    clipped_raster, clipped_transform = rasterio.mask.mask(raster_obj, shp_geometry, crop=True)

    array = numpy.asarray(clipped_raster)
    array[array > 1000000000] = numpy.nan       # change the comparator to git rid of the fill value
    array = array.flatten()
    array = array[~numpy.isnan(array)]
    mean = array.mean()

    return mean


nc_to_geotiff(r'/Users/rileyhales/Documents/sampledata/n41w112_30m/GLDAS_NOAH025_M.A201902.021.nc4', 'Tair_f_inst', r'/Users/rileyhales/Documents/sampledata/')

spatialaverage(r'/Users/rileyhales/Documents/sampledata/n41w112_30m/n41w112_30m.tif', r'/Users/rileyhales/Documents/sampledata/shapefile/shapefile.shp')
