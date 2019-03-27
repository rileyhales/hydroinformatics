def spatialaverage():
    """
    Spatial average returns the arithmetic mean of the values in a netcdf raster within the boundaries of a shapefile
    """
    import fiona
    import rasterio
    from rasterio.mask import mask
    import numpy

    # rasterpath = r'/Users/rileyhales/Documents/sampledata/n41w112_30m/n41w112_30m.tif'
    rasterpath = r'/Users/rileyhales/Documents/sampledata/n41w112_30m/GLDAS_NOAH025_M.A201902.021.nc4'
    raster_obj = rasterio.open(rasterpath)
    print(raster_obj)
    print(type(raster_obj))

    # shp_path = r'/Users/rileyhales/Documents/sampledata/shapefile/shapefile.shp'
    shp_path = r'/Users/rileyhales/Documents/sampledata/shapefilegcs/shapefile_Project.shp'
    shp_object = fiona.open(shp_path, 'r')
    shp_geometry = [feature["geometry"] for feature in shp_object]
    print(shp_geometry)

    clipped_raster, clipped_transform = rasterio.mask.mask(raster_obj, shp_geometry, crop=True)

    x = numpy.asarray(clipped_raster)
    x[x > 1000000000] = numpy.nan
    x = x.flatten()
    x = x[~numpy.isnan(x)]

    print(x.mean())

    return


spatialaverage()
