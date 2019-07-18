#!/usr/bin/env bash
# $1 geoserver admin username (admin)
# $2 geoserver admin passwrod (geoserver)
# $3 path to the zip archive (/path/to/zip/username.zip)
# $4 geoserver url (https://tethys.byu.edu/geoserver)
# $5 name of the tethys app (gldas)
# $6 geoserver datastore name (use the name of the user uploading the shapefile)
curl -v -u $1:$2 -XPUT -H "Content-type: application/zip" --data-binary @$3 $4/rest/workspaces/$5/datastores/$6/file.shp