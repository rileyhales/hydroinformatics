import os
import json
import shapefile
from osgeo import ogr
from osgeo import osr


def geojson_to_shp(geojson, savepath):
    # turn the geojson into a dictionary if it isn't
    if not isinstance(geojson, dict):
        try:
            geojson = json.loads(geojson)
        except json.JSONDecodeError:
            raise Exception('Unable to extract a dictionary or json like object from the argument geojson')

    # create the shapefile
    fileobject = shapefile.Writer(target=savepath, shpType=shapefile.POLYGON, autoBalance=True)

    # label all the columns in the .dbf
    geomtype = geojson['features'][0]['geometry']['type']
    if geojson['features'][0]['properties']:
        for attribute in geojson['features'][0]['properties']:
            fileobject.field(str(attribute), 'C', '30')
    else:
        fileobject.field('Name', 'C', '50')

    # add the geometry and attribute data
    for feature in geojson['features']:
        if geomtype == 'Polygon':
            fileobject.poly(polys=feature['geometry']['coordinates'])
        elif geomtype == 'MultiPolygon':
            for i in feature['geometry']['coordinates']:
                fileobject.poly(polys=i)
        if feature['properties']:
            fileobject.record(**feature['properties'])
        else:
            fileobject.record('unknown')

    # create a prj file
    with open(savepath + '.prj', 'w') as prj:
        prj.write('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
                  'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]')

    fileobject.close()
    return


# todo
# def shp_to_geojson(shp_path):
#     # get kwargs and processes args
#     shp_base_path = os.path.split(shp_path)[0]
#     shp_name = os.path.split(shp_path)[1]
#
#     # read the shapfile
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#     raw_shp_src = driver.Open(shp_path)
#     raw_shp = raw_shp_src.GetLayer()
#
#     # handle the projections
#     in_prj = raw_shp.GetSpatialRef()
#     out_prj = osr.SpatialReference().ImportFromEPSG('4326')
#     coordTrans = osr.CoordinateTransformation(in_prj, out_prj)
#
#     # make a reprojected shapefile
#     reprojected_shp_src = driver.CreateDataSource(shp_base_path)
#     reprojected_shp = reprojected_shp_src.CreateLayer(shp_name.encode('utf-8'), geom_type=ogr.wkbLineString)
#
#     raw_shp_lyr_def = raw_shp.GetLayerDefn()
#     for i in range(0, raw_shp_lyr_def.GetFieldCount()):
#         field_def = raw_shp_lyr_def.GetFieldDefn(i)
#         if field_def.name in ['COMID', 'watershed', 'subbasin']:
#             reprojected_shp.CreateField(field_def)
#
#     # get the output layer's feature definition
#     reprojected_shp_lyr_def = reprojected_shp.GetLayerDefn()
#
#     # loop through the input features
#     in_feature = raw_shp.GetNextFeature()
#     while in_feature:
#         # get the input geometry
#         geom = in_feature.GetGeometryRef()
#         # reproject the geometry
#         geom.Transform(coordTrans)
#         # create a new feature
#         out_feature = ogr.Feature(reprojected_shp_lyr_def)
#         # set the geometry and attribute
#         out_feature.SetGeometry(geom)
#         out_feature.SetField('COMID', in_feature.GetField(in_feature.GetFieldIndex('COMID')))
#         # add the feature to the shapefile
#         reprojected_shp.CreateFeature(out_feature)
#         # dereference the features and get the next input feature
#         out_feature = None
#         in_feature = raw_shp.GetNextFeature()
#
#     fc = {
#         'type': 'FeatureCollection',
#         'features': []
#     }
#
#     for feature in reprojected_shp:
#         fc['features'].append(feature.ExportToJson(as_object=True))
#
#     with open(shp_path.replace('.shp', '.json'), 'w') as f:
#         json.dump(fc, f)
#
#     return
