# ncTools
A collection of functions for viewing and manipulating netCDF files

Each of these functions are written to accept the same possible parameters.
* ***file_path***: the path to a specific netCDF file including the extension.
* ***dir_path***: the path to a directory that contains ONLY netCDF files. Functions requiring this parameter will execute code that interacts with all these files.
* ***save_dir_path***: the path to a directory where you want to save the output files produced by the method you specified.
* ***var***: the name of a variable that you want the function to focus on. This should be the name as it appears in the file, not a full/long name that is listed in the attributes.
* ***coords***: a tuple that contains the locations of a point in (lat, lon) format.
* ***rasterpath***: a string path to the raster dataset to be used in the function. Must be GeoTiff format in a geographic coordinate system (WGS 1984)

### timeseries_netcdfDir.py
Give it a directory of netCDF4 files broken up by timestep and creates a timeseries of each variable based on parameters
you specify. Supports compression.

### inspectcontents.py
You give it a file and it has the commands written to view variables and dimensions and their attributes.

### variablebounds.py
You give it a file path and it returns a dictionary of the min/max values for every variable in the format {'name of variable': 'min,max'}

### timeseriespt.py
At a given coords location, it creates a timeseries of points for a specific var from all the netCDF4 files in datadir for given time period (following the nasa GLDAS naming conventions) (or coming soon: all the timesteps of a netCDF with many time steps for a variable).

### geoprocessing.py
Contains python functions for simple geoprocessing operatiosn you need to perform on netcdf formatted data.
* ***spatialaverage.py***: Intended to be used in conjunction with netcdf_to_geotiff.py functions. Contains a function that takes a geotiff raster and a shapefile with polygon boundaries, calculates the average of the data in the geotiff's band within the boundaries marked by the shapefile.

### netcdf_to_geotiff.py
Contains functions for taking netcdfs and creating geotiffs out of them in the following permutations:
* ***nc1_to_gtiff***: Accepts a single netcdf file and writing the data from 1 variable to a 1 band geotiff.
* ***ncAll_to_gtiff***: Accepts a single netcdf file and writes the data from all variables to a geotiff with as many bands as variables.
* ***ncDir_to_MBgtiff***: Accepts a file path to a directory of netcdf files representing different time steps of the same data and combines them into a single geotiff where each timestep is in a different band.
