def nc_to_geotiff(file_path, var, save_dir_path):
    """
    This script accepts a netcdf file in a geographic coordinate system, specifically the NASA GLDAS netcdfs, and
    extracts the data from one variable and the lat/lon steps to create a geotiff of that information.
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
    array = array[::-1]       # vertically flip the array so the orientation is right (you just have to, try it without)

    # Creates geotiff raster file (filepath, x-dimensions, y-dimensions, number of bands, datatype)
    geotiffdriver = gdal.GetDriverByName('GTiff')
    new_geotiff = geotiffdriver.Create(save_dir_path + 'geotiff.tif', len(lon), len(lat), 1, gdal.GDT_Float32)

    # geotransform (sets coordinates) = (x-origin(left), x-width, x-rotation, y-origin(top), y-rotation, y-width)
    yorigin = lat.max()
    xorigin = lon.min()
    xres = lat[1] - lat[0]
    yres = lon[1] - lon[0]
    new_geotiff.SetGeoTransform((xorigin, xres, 0, yorigin, 0, -yres))

    # Set the projection of the geotiff (Projection EPSG:4326, Geographic Coordinate System WGS 1984 (degrees lat/lon)
    new_geotiff.SetProjection(osr.SRS_WKT_WGS84)

    # actually write the data array to the tiff file and save it
    new_geotiff.GetRasterBand(1).WriteArray(array)      # write band to the raster (variable array)
    new_geotiff.FlushCache()                            # write to disk

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
    del clipped_raster, raster_obj
    array[array < -1000] = numpy.nan        # If you have fill values, change the comparator to git rid of it
    array = array.flatten()
    array = array[~numpy.isnan(array)]
    mean = array.mean()
    print(mean)

    return mean

nc_to_geotiff(r'/Users/rileyhales/Documents/sampledata/n41w112_30m/GLDAS_NOAH025_M.A201902.021.nc4', 'Tair_f_inst', r'/Users/rileyhales/Documents/nctools/')
spatialaverage(r'/Users/rileyhales/Documents/nctools/geotiff.tif', r'/Users/rileyhales/Documents/sampledata/shapefilegcs/shapefile_Project.shp')
