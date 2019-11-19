import os
import datetime as dt
import netCDF4
import numpy
import rasterio
import rasterstats
from rasterio.enums import Resampling


def netcdf_to_tiff(netcdfs, var):
    # create a list of all the files
    files = os.listdir(netcdfs)
    files = [nc for nc in files if nc.endswith('.nc4')]
    files.sort()

    # return items
    values = []

    # open the netcdf and get metadata
    nc_obj = netCDF4.Dataset(os.path.join(netcdfs, files[0]), 'r')
    lat = nc_obj.variables['lat'][:]
    lon = nc_obj.variables['lon'][:]
    units = nc_obj[var].__dict__['units']
    affine = rasterio.transform.from_origin(lon.min(), lat.max(), lat[1] - lat[0], lon[1] - lon[0])
    nc_obj.close()

    vectorpath = os.path.join('/Users/rileyhales/NLDAS/shapefile/Cibolo_Creek_Upstream.shp')

    # Read raster dimensions only once to apply to all rasters
    path = os.path.join(netcdfs, files[0])
    raster_dim = rasterio.open(path)
    width = raster_dim.width
    height = raster_dim.height
    lon_min = raster_dim.bounds.left
    lon_max = raster_dim.bounds.right
    lat_min = raster_dim.bounds.bottom
    lat_max = raster_dim.bounds.top

    # Geotransform for each
    geotransform = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width, height)

    # extract the timeseries by iterating over each netcdf
    for nc in files:
        path = os.path.join(netcdfs, nc)

        # open the netcdf and get the data array
        nc_obj = netCDF4.Dataset(path, 'r')
        time = dt.datetime.strptime(nc_obj['time'].__dict__['begin_date'], "%Y%m%d")
        nc_obj.close()

        # CREATE A GEOTIFF
        src = rasterio.open(path)
        file_array = src.read(1)

        with rasterio.open(
                '/Users/rileyhales/NLDAS/tifs/' + nc + '.tif',
                'w',
                driver='GTiff',
                height=file_array.shape[0],
                width=file_array.shape[1],
                count=1,
                dtype=file_array.dtype,
                nodata=numpy.nan,
                crs='+proj=latlong',
                transform=geotransform,
        ) as dst:
            dst.write(file_array, 1)

        # Geotransform for each 24-hr raster (east, south, west, north, width, height)
        geotransform_resample = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, width * 5,
                                                               height * 5)

        # RESAMPLE THE GEOTIFF
        with rasterio.open('/Users/rileyhales/NLDAS/tifs/' + nc + '.tif') as dataset:
            data = dataset.read(
                out_shape=(height * 5, width * 5),
                resampling=Resampling.nearest
            )

        # Convert new resampled array from 3D to 2D
        data = numpy.squeeze(data, axis=0)

        # Specify the filepath of the resampled raster
        resample_filepath = os.path.join('/Users/rileyhales/NLDAS/resampleds/', nc + '.tif')

        # Save the GeoTIFF
        with rasterio.open(
                resample_filepath,
                'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                nodata=numpy.nan,
                crs='+proj=latlong',
                transform=geotransform_resample,
        ) as dst:
            dst.write(data, 1)

        stats = rasterstats.zonal_stats(vectorpath, '/Users/rileyhales/NLDAS/resampleds/', nc + '.tif',
                                        affine=affine, nodata=numpy.nan, stats="mean")
        tmp = [i['mean'] for i in stats if i['mean'] is not None]
        values.append((time, sum(tmp) / len(tmp)))

        nc_obj.close()

    return values, units
