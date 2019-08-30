# Hydroinformatics

A series of scripts to show you how to do whatever you need to do as a researach assistant for Dr Nelson

© Riley Hales, 2019, BSD 3-Clause

## Quick Reference

This command asks you to specify:
* Geoserver Username and Password. If you have not changed it, the default is admin and geoserver.
* Name of the Zip Archive you're uploading. Be sure you spell it correctly and that you put it in each of the 2 places it is asked for.
* Hostname. The host website, e.g. ```tethys.byu.edu```.
* The Workspace URI. The URI that you specified when you created the new workspace through the web interface. If you followed these instructions it should be ```gldas```.

~~~~
curl -v -u [user]:[password] -XPUT -H "Content-type: application/zip" --data-binary @[name_of_zip].zip https://[hostname]/geoserver/rest/workspaces/[workspaceURI]/datastores/[name_of_zip]/file.shp
~~~~