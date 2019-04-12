def rastermask_average_rasterio(rasterpath, shape_path):
    """
    Description: A function that masks a raster by the extents of a shapefile and returns the arithmetic mean of the
        raster's values in that area. Assumes the shapefile and raster are in the same geographic coordinate system
    Dependencies: fiona, rasterio, numpy
    Params: View README.md
    Returns: computer mean value
    Author: Riley Hales, RCH Engineering, April 2019
    """
    import fiona
    import rasterio
    from rasterio.mask import mask
    import numpy

    # read the raster into a rasterio object
    raster_obj = rasterio.open(rasterpath)
    # from rasterio.plot import show
    # rasterio.plot.show(raster_obj) # optional command to show a plot of the new raster

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


def rastermask_average_gdal(rasterpath, shapepath):
    """
    Description: A function to mask/clip a raster by the boundaries of a shapefile and computer the average value of the
        resulting raster
    Dependencies: gdal, gdalnumeric
    Params: View README.md
    Returns: computer mean value
    Author: Riley Hales, RCH Engineering, April 2019
    """
    import gdal
    import gdalnumeric

    # open the raster as a gdal object and a gdalnumeric array
    raster = gdal.Open(rasterpath)
    raster_array = gdalnumeric.LoadFile(rasterpath)
    geotransform = raster.GetGeoTransform()
    projection = raster.GetProjection()

    mean = 0

    return mean


rastermask_average_rasterio(r'/Users/rileyhales/Documents/nctools/geotiff.tif', r'/Users/rileyhales/Documents/sampledata/shapefilegcs/shapefile_Project.shp')
