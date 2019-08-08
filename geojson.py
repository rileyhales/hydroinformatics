import json
import shapefile


class GeoJ:
    geometryType = ''
    columnsList = []
    __attributesPerF = []
    attributes = []
    geometries = []

    shpFileObj = None

    # The constructor which basically needs the geoJSON file+path as an argument
    def __init__(self, geoJFile):
        # This try statement makes sure that the geojson file exists and it is in JSON structure
        try:
            self.geoJFile = open(geoJFile)
        except IOError:
            print("Error: can not find file. Make sure the file name and path are correct")
        else:
            try:
                self.geoJObj = json.load(self.geoJFile)
            except ValueError:
                print("Error: the file is not in JSON structure")
            else:
                # If everything is fine, the __parseGeoJ private method will
                # collect attributes and geometries from the geoJSON file
                self.__parseGeoJ()

    def __parseGeoJ(self):

        self.geometryType = self.geoJObj['features'][0]['geometry']['type']

        self.columnsList = self.geoJObj['features'][0]['properties'].keys()

        for i in self.geoJObj['features']:

            if i['geometry']['type'] == self.geometryType:
                self.geometries.append(i['geometry']['coordinates'])
                self.attributes.append([str(i['properties'][str(j)]) for j in self.columnsList])

    # This method along with the following private methods will create a shapefile
    # from the collected attributes and geometries from the geoJSON file
    def to_shapefile(self, savepath):

        if self.geometryType == 'Point':
            self.__createPoint(savepath)
        elif self.geometryType == 'LineString':
            self.__createLine(savepath)
        elif self.geometryType == 'Polygon':
            self.__createPolygon(savepath)
        elif self.geometryType == 'MultiPolygon':
            self.__createMultiPolygon(savepath)
        else:
            print('Cannot proceed. Geometry type ' + self.geometryType + ' is not supported in this program')
            return

        # Calling the __createPrjFile method to create a .prj file
        self.__createPrjFile(savepath)

        # Saving the shape file, which creates .shp, .shx, and .dbf files
        self.shpFileObj.close()

    # This method is used to create points shapefile
    def __createPoint(self, savepath):

        self.shpFileObj = shapefile.Writer(target=savepath, shpType=shapefile.POINT, autoBalance=True)
        self.__createColumns()

        for i in self.geometries:
            self.shpFileObj.point(i[0], i[1])

        for j in self.attributes:
            self.shpFileObj.record(*j)

    # This method is used to create lines shapefile
    def __createLine(self, savepath):

        self.shpFileObj = shapefile.Writer(target=savepath, shpType=shapefile.POLYLINE, autoBalance=True)
        self.__createColumns()

        for i in self.geometries:
            self.shpFileObj.line(parts=[i])

        for j in self.attributes:
            self.shpFileObj.record(*j)

    # This method is used to create polygons shapefile
    def __createPolygon(self, savepath):
        self.shpFileObj = shapefile.Writer(target=savepath, shpType=shapefile.POLYGON, autoBalance=True)
        self.__createColumns()

        for i in self.geometries:
            self.shpFileObj.poly(polys=i)

        for j in self.attributes:
            self.shpFileObj.record(j)

    # This method is used to create multipolygons shapefile
    def __createMultiPolygon(self, savepath):
        self.shpFileObj = shapefile.Writer(target=savepath, shpType=shapefile.POLYGON, autoBalance=True)
        self.__createColumns()

        # for i in self.geometries:
        #     for j in i:
        #         self.shpFileObj.poly(polys=j)

        # for k in self.attributes:
        #     self.shpFileObj.record(*k)

        for feature in self.geoJObj['features']:
            for i in feature['geometry']['coordinates']:
                self.shpFileObj.poly(polys=i)
            self.shpFileObj.record(**feature['properties'])

    # This method is used to create the columns names read from the geoJSON file
    def __createColumns(self):
        for i in self.columnsList:
            # Field names cannot be unicode.
            # That is why I cast it to string.
            self.shpFileObj.field(str(i), 'C', '50')

    # This method currently creates a .prj file with WGS84 projection
    def __createPrjFile(self, savepath):
        with open(savepath + '.prj', 'w') as prj:
            prj.write('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
                      'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]')


gj = GeoJ('/Users/rileyhales/thredds/centralamerica.geojson')
gj.to_shapefile('/Users/rileyhales/thredds/cashptest')
