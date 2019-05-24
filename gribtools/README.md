xarray with 

source = rasterio.open('path to a grib file')
source.meta # metadata about the object you just opened
source.read(bandnumber) # gets you the array of data in the band number you gave it.
						# use qgis to inspect the contents of the grib file and you can read a printout of all the band numbers and thier information
