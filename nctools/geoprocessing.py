def rastermask_average_rasterio(rasterpath, shape_path):
    """
    Description: A function that masks a raster by the extents of a shapefile and returns the arithmetic mean of the
        raster's values in that area. Assumes the shapefile and raster are in the same geographic coordinate system
    Dependencies: fiona, rasterio, numpy
    Params: View README.md
    Returns: computed mean value
    Author: Riley Hales, RCH Engineering, April 2019
    """
    import fiona
    import rasterio
    from rasterio.mask import mask
    import numpy

    # read the raster (eg a tiff) into a rasterio object
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


def rastermask_average_gdalwarp(rasterpath, shapepath):
    """
    Description: A function to mask/clip a raster by the boundaries of a shapefile and computer the average value of the
        resulting raster
    Dependencies: gdal, gdalnumeric, numpy
    Params: View README.md
    Returns: mean value of an array within a shapefile's boundaries
    Author: Riley Hales, RCH Engineering, April 2019
    """
    import gdal
    import gdalnumeric
    import numpy

    inraster = gdal.Open(rasterpath)
    outraster = r'/Users/rileyhales/Documents/sampledata/gldalwarp.tif'  # your output raster file
    clippedraster = gdal.Warp(outraster, inraster, format='GTiff', cutlineDSName=shapepath, dstNodata=numpy.nan)
    array = gdalnumeric.DatasetReadAsArray(clippedraster)
    array = array.flatten()
    array = array[~numpy.isnan(array)]
    mean = array.mean()
    print(mean)

    return mean


rastermask_average_gdalwarp(r'/Users/rileyhales/Documents/sampledata/gldasgeotiff/gldasgeotiff.tif', r'/Users/rileyhales/Documents/sampledata/shapefilegcs/shapefile_Project.shp')


def rastermask_average_gdal(rasterpath, shapepath):
    """
    Description: A function to mask/clip a raster by the boundaries of a shapefile and computer the average value of the
        resulting raster
    Dependencies: gdal, gdalnumeric
    Params: View README.md
    Returns: computed mean value
    Author: Riley Hales, RCH Engineering, April 2019
    """
    import gdal
    import PIL.Image as Image
    import PIL.ImageDraw as ImageDraw
    import gdalnumeric
    import ogr
    import os

    # open the raster as a gdal object to get metadata from it
    raster = gdal.Open(rasterpath)              # a gdal Dataset object
    geotransform = raster.GetGeoTransform()     # tuple (minX, Xstep, row-rotation, maxY, column rotation, Ystep)
    projection = raster.GetProjection()         # WKT string (print it)
    del raster

    # open the raster as an array, the geoprocessing math is done on the array
    raster_array = gdalnumeric.LoadFile(rasterpath)

    # create the masking raster from the shapefile
    mask_shp = ogr.Open(shapepath)
    layer = mask_shp.GetLayer(os.path.split(os.path.splitext(shapepath)[0])[1])
    polygon = layer.GetNextFeature()    # the polygon masking information ogr.Feature object
    extents = layer.GetExtent()         # tuple (minX, maxX, minY, maxY)

    # Index of points = distance between upperleft x,y and chosen x,y divided by step length
    min_x_index = int(abs(geotransform[0] - extents[0])/geotransform[1])
    max_y_index = int(abs(geotransform[3] - extents[3])/geotransform[5])
    max_x_index = int(abs(geotransform[0] - extents[1])/geotransform[1])
    min_y_index = int(abs(geotransform[3] - extents[2])/geotransform[5])
    # slice the raster array to contain only the data in the extents of the shapefile
    clip = raster_array[min_y_index:max_y_index, min_x_index:max_x_index]
    print(clip)
    print(clip.shape)

    def world2Pixel(geoMatrix, x, y):
        """
        Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
        the pixel location of a geospatial coordinate
        """
        ulX = geoMatrix[0]
        ulY = geoMatrix[3]
        xDist = geoMatrix[1]
        yDist = geoMatrix[5]
        rtnX = geoMatrix[2]
        rtnY = geoMatrix[4]
        pixel = int((x - ulX) / xDist)
        line = int((ulY - y) / xDist)
        return pixel, line

    points = []
    pixels = []
    geom = polygon.GetGeometryRef()
    pts = geom.GetGeometryRef(0)
    for p in range(pts.GetPointCount()):
        points.append((pts.GetX(p), pts.GetY(p)))
    for p in points:
        pixels.append(world2Pixel(geotransform, p[0], p[1]))
    print(pixels)
    rasterPoly = Image.new("L", (max_x_index - min_x_index, max_y_index - min_y_index), 1)
    rasterize = ImageDraw.Draw(rasterPoly)
    rasterize.polygon(pixels, 0)

    mask = gdalnumeric.fromstring(rasterPoly.tostring(), 'b')
    mask.shape = rasterPoly.im.size[1], rasterPoly.im.size[0]
    print(mask)

    return
