# ncTools
A collection of functions for viewing and manipulating netCDF files

Each of these functions are written to accept the same possible parameters.
* ***file_path***: the path to a specific netCDF file including the extension.
* ***dir_path***: the path to a directory that contains ONLY netCDF files. Functions requiring this parameter will execute code that interacts with all these files.
* ***save_dir_path***: the path to a directory where you want to save the output files produced by the method you specified.
* ***var***: the name of a variable that you want the function to focus on. This should be the name as it appears in the file, not a full/long name that is listed in the attributes.
* ***coords***: a tuple that contains the locations of a point in (lat, lon) format.

### timeseries_netcdfDir.py
Give it a directory of netCDF4 files broken up by timestep and creates a timeseries of each variable based on parameters
you specify. Supports compression.

### inspectcontents.py
You give it a file and it has the commands written to view variables and dimensions and their attributes.

### variablebounds.py
You give it a file path and it returns a dictionary of the min/max values for every variable in the format {'name of variable': 'min,max'}

### timeseriespt.py
you give it a coords variable and the directory containing the individual netCDF files (or coming soon: all the timesteps of a netCDF with many time steps for a variable). 