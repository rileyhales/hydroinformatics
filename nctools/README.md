# ncTools
A collection of functions for viewing and manipulating netCDF files.  
Copyright [Riley Hales](https://www.rileyhales.com), RCH Engineering, 2018

## Making a netcdf OGC Services Compliant
A netcdf what complies with the Common Data Model (CDM) standards can supply an OGC service with data. For full details see [this UCAR page describing the CDM](https://www.unidata.ucar.edu/software/thredds/current/netcdf-java/CDM/).

In summary, some important features necessary for a netcdf to become compliant are:
1. 2 Coordinate Dimensions, lat and lon. Their size is the number of steps across the grid.
2. 2 Coordinate Variables, lat and lon, whose arrays contain the lat/lon values of the grid points.
    These variables only require the corresponding lat or lon dimension.
3. 1 time dimension whose length is the number of time steps
4. 1 time variable whose array contains the difference in time between steps using the units given in the metadata. The begin_date attribute must specify the time in YYYYMMDDHH format.
5. Each variable requires the the time and Coordinate Dimensions, in that order (time, lat, lon)
6. Each variable has the long_name, units, standard_name property values correct
7. The variable property coordinates = "lat lon" or else is blank/doesn't exist
8. The array of variable information as exactly the same dimensions as the x/y coordinate variables.

## Using NetCDF Markup Language
You can aggregate date from many NetCDF's on the fly with Thredds and Panoply and other softwares using netcdf markup language, .ncml. Some examples are in the ncml document in this directory. A more full explanation of ncml is at [this UCAR page](https://www.unidata.ucar.edu/software/thredds/current/netcdf-java/ncml/) and you can google examples.

## Notes about these functions
Most functions require at least one of the following parameters:
* ***file_path***: the path to a specific netCDF file including the extension.
* ***dir_path***: the path to a directory that contains ONLY netCDF files. Functions requiring this parameter will execute code that interacts with all these files.
* ***save_dir_path***: the path to a directory where you want to save the output files produced by the method you specified.
* ***var***: the name of a variable that you want the function to focus on. This should be the name as it appears in the file, not a full/long name that is listed in the attributes.
* ***coords***: a tuple that contains the locations of a point in (lat, lon) format.

Some less common parameters include:
* ***baserasterpath***: a string path to the raster dataset to be used in the function. Must be GeoTiff format in a geographic coordinate system (WGS 1984)
* ***outrasterpath***: a string path where you want to save the raster dataset created by the function. Must be GeoTiff format in a geographic coordinate system (WGS 1984)

### inspectcontents.py
* ***show_contents***: You give it a file and it has the commands written to view variables and dimensions and their attributes.
* ***variablebounds.py***: You give it a file path and it returns a dictionary of the min/max values for every variable in the format {'name of variable': 'min,max'}

### timeseries.py
* ***ts_pt_plot***: At a given coords location, it creates a timeseries of points for a specific var from all the netCDF4 files in datadir for given time period (following the nasa GLDAS naming conventions) (or coming soon: all the timesteps of a netCDF with many time steps for a variable).
* ***timeseries_netcdfDir.py***: Give it a directory of netCDF4 files broken up by timestep and creates a timeseries of each variable based on parameters you specify. Supports compression.

### geoprocessing.py
Contains python functions for simple geoprocessing operatiosn you need to perform on netcdf formatted data.
* ***rastermask_average_rasterio***: Uses the rasterio package to compute the average of a geotiff within the extents of a bounding shapefile. Intended to be used in conjunction with netcdf_to_geotiff.py
* ***rastermask_average_gdalwarp***: Uses the GDAL package to compute the average of a geotiff within the extents of a bounding shapefile. Intended to be used in conjunction with netcdf_to_geotiff.py

### netcdf_to_geotiff.py
Contains functions for taking netcdfs and creating geotiffs out of them in the following permutations:
* ***nc1_to_gtiff***: Accepts a single netcdf file and writing the data from 1 variable to a 1 band geotiff.
* ***ncAll_to_gtiff***: Accepts a single netcdf file and writes the data from all variables to a geotiff with as many bands as variables.
* ***ncDir_to_MBgtiff***: Accepts a file path to a directory of netcdf files representing different time steps of the same data and combines them into a single geotiff where each timestep is in a different band.

### nc_ogcwms.py
Contains functions to take netcdfs from a raw to a usable form 
* ***nc_georeference***: Takes a LIS forecast output netcdf and turns it into a WMS recognizable format. Not functional.
