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
    Returns: computed mean value
    Author: Riley Hales, RCH Engineering, April 2019
    """
    import gdal
    import gdalnumeric
    import ogr

    # open the raster as a gdal object to get metadata from it
    raster = gdal.Open(rasterpath)
    print(type(raster))
    geotransform = raster.GetGeoTransform()
    print(geotransform)
    print(type(geotransform))
    projection = raster.GetProjection()
    print(projection)
    print(type(projection))
    del raster

    # open the raster as an array, the geoprocessing math is done on the array
    raster_array = gdalnumeric.LoadFile(rasterpath)

    # create the masking raster from the shapefile
    mask_shp = ogr.Open(shapepath)

    mean = 0

    return mean


rastermask_average_gdal(r'/Users/rileyhales/Documents/sampledata/gldasgeotiff/gldasgeotiff.tif')

"""
def main( shapefile_path, raster_path ):
    # Create an OGR layer from a boundary shapefile
    shapef = ogr.Open(shapefile_path)
    lyr = shapef.GetLayer( os.path.split( os.path.splitext( shapefile_path )[0] )[1] )
    poly = lyr.GetNextFeature()

    # Map points to pixels for drawing the
    # boundary on a blank 8-bit,
    # black and white, mask image.
    points = []
    pixels = []
    geom = poly.GetGeometryRef()
    pts = geom.GetGeometryRef(0)
    for p in range(pts.GetPointCount()):
      points.append((pts.GetX(p), pts.GetY(p)))
    for p in points:
      pixels.append(world2Pixel(geoTrans, p[0], p[1]))
    rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
    rasterize = ImageDraw.Draw(rasterPoly)
    rasterize.polygon(pixels, 0)
    mask = imageToArray(rasterPoly)

    # Clip the image using the mask
    clip = gdalnumeric.choose(mask, (clip, 0)).astype(gdalnumeric.uint8)

    # Convert the layer extent to image pixel coordinates
    minX, maxX, minY, maxY = lyr.GetExtent()
    ulX, ulY = world2Pixel(geoTrans, minX, maxY)
    lrX, lrY = world2Pixel(geoTrans, maxX, minY)

    # Calculate the pixel size of the new image
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)

    clip = srcArray[:, ulY:lrY, ulX:lrX]

    #
    # EDIT: create pixel offset to pass to new image Projection info
    #
    xoffset =  ulX
    yoffset =  ulY
    print "Xoffset, Yoffset = ( %f, %f )" % ( xoffset, yoffset )

    # Create a new geomatrix for the image
    geoTrans = list(geoTrans)
    geoTrans[0] = minX
    geoTrans[3] = maxY
"""