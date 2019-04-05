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

    return mean


spatialaverage(r'/Users/rileyhales/Documents/nctools/geotiff.tif', r'/Users/rileyhales/Documents/sampledata/shapefilegcs/shapefile_Project.shp')
