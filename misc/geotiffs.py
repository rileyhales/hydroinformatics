import os
import rasterio
from rasterio.enums import Resampling
import numpy


def resample(tif_path, resample, **kwargs):
    # process args - get list of tifs
    if os.path.isdir(tif_path):
        geotiffs = os.listdir(tif_path)
        geotiffs = [i for i in geotiffs if any([i.endswith('.tif'), i.endswith('.geotiff'), i.endswith('gtif')])]
        geotiffs.sort()
    elif os.path.isfile(tif_path):
        split = os.path.split(tif_path)
        tif_path = split[0]
        geotiffs = [split[1]]

    # process kwargs
    save_dir = kwargs.get('save_dir', tif_path)
    delete_sources = kwargs.get('delete_sources', False)

    # Create the geotransform
    geotransform = kwargs.get('geotransform', None)
    if not geotransform:
        with rasterio.open(os.path.join(tif_path, geotiffs[0])) as ds:
            bd = ds.bounds 
            geotransform = rasterio.transform.from_bounds(bd.left, bd.bottom, bd.right, bd.top,
                                                          ds.width * resample, ds.height * resample)

    # Loop over all the geotiffs
    for tif in geotiffs:
        path = os.path.join(tif_path, tif)
        with rasterio.open(path) as ds:
            data = ds.read(
                out_shape=(ds.height * resample, ds.width * resample),
                resampling=Resampling.nearest
            )

        # Convert new resampled array from 3D to 2D
        data = numpy.squeeze(data, axis=0)

        # Specify the filepath of the resampled raster
        save_path = os.path.join(save_dir, 'Resampled_' + tif)

        # Save the GeoTIFF
        with rasterio.open(
                save_path,
                'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                nodata=numpy.nan,
                crs='+proj=latlong',
                transform=geotransform,
        ) as dst:
            dst.write(data, 1)

        if delete_sources:
            os.remove(path)

    return
