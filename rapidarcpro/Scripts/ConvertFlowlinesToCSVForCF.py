# Import arcpy module
import arcpy
import csv
from numpy import array, isnan
import os


class ConvertFlowlinesToCSVForCF(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Convert Flowlines to CSV for CF"
        self.description = ("Convert flowlines to csv valid for RAPID CF script")
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_drainage_line = arcpy.Parameter(
            displayName='Input Drainage Line Features',
            name='in_drainage_line_features',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')
        in_drainage_line.filter.list = ['Polyline']

        param1 = arcpy.Parameter(name="stream_ID",
                                 displayName="Stream ID",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="Field"
                                 )
        param1.parameterDependencies = ["in_drainage_line_features"]
        param1.filter.list = ['Short', 'Long']

        param2 = arcpy.Parameter(name='out_comid_lat_lon_z',
                                 displayName='Output comid_lat_lon_z file',
                                 direction='Output',
                                 parameterType='Required',
                                 datatype='DEFile')

        params = [in_drainage_line, param1, param2]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[2].altered:
            (dirnm, basenm) = os.path.split(parameters[2].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[2].value = os.path.join(dirnm, "{}.csv".format(basenm))

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        # Script arguments
        Input_Features = parameters[0].valueAsText
        streamID = parameters[1].valueAsText
        Output_Table = parameters[2].valueAsText
        Intermediate_Feature_Points = os.path.join("in_memory", "flowline_centroid_points")
        Intermediate_Feature_Points_Projected = os.path.join(arcpy.env.scratchGDB, "flowline_centroid_points_project")

        # Process: Feature To Point
        arcpy.AddMessage("Converting flowlines to points ...")
        arcpy.FeatureToPoint_management(Input_Features, Intermediate_Feature_Points, "CENTROID")

        # Process: Make sure projection is GCS_WGS_1984
        dsc = arcpy.Describe(Intermediate_Feature_Points)
        if dsc.spatialReference.Name == "Unknown":
            messages.addErrorMessage("Unknown Spatial Reference. Please fix to continue.")
        elif dsc.spatialReference.Name != "GCS_WGS_1984":
            arcpy.AddMessage("Projecting to GCS_WGS_1984 from %s ..." % dsc.spatialReference.Name)
            arcpy.Project_management(in_dataset=Intermediate_Feature_Points,
                                     out_dataset=Intermediate_Feature_Points_Projected,
                                     out_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]",
                                     )
            arcpy.Delete_management(Intermediate_Feature_Points)
        else:
            Intermediate_Feature_Points_Projected = Intermediate_Feature_Points

        # Process: Add XY Coordinates
        arcpy.AddMessage("Adding XY coordinates to points ...")
        arcpy.AddXY_management(Intermediate_Feature_Points_Projected)

        # write only desired fields to csv
        arcpy.AddMessage("Writing output to csv ...")
        original_field_names = [f.name for f in arcpy.ListFields(Intermediate_Feature_Points_Projected)]
        # arcpy.AddMessage("Field names: %s" % original_field_names)
        # COMID,Lat,Lon,Elev_m
        actual_field_names = [streamID, "", ""]
        needed_field_names = ['point_y', 'point_x', 'point_z']
        elevation_exists = False
        for original_field_name in original_field_names:
            original_field_name_lower = original_field_name.lower()
            if original_field_name_lower == needed_field_names[0]:
                actual_field_names[1] = original_field_name
            elif original_field_name_lower == needed_field_names[1]:
                actual_field_names[2] = original_field_name
            elif original_field_name_lower == needed_field_names[2]:
                actual_field_names.append(original_field_name)
                elevation_exists = True

        # check to make sure all fields exist
        for index, field_name in enumerate(actual_field_names):
            if field_name == "":
                messages.addErrorMessage("Field name %s not found." % needed_field_names[index - 1])
                raise arcpy.ExecuteError

        # print valid field names to table
        with open(Output_Table, 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['COMID', 'Lat', 'Lon', 'Elev_m'])
            with arcpy.da.SearchCursor(Intermediate_Feature_Points_Projected, actual_field_names) as cursor:
                for row in cursor:
                    # if no elevation found, append zero
                    if not elevation_exists:
                        row += (0,)
                    # make sure all values are valid
                    np_row = array(row)
                    np_row[isnan(np_row)] = 0
                    writer.writerow([int(np_row[0])] + np_row[1:].tolist())

        # delete intermediate layer
        arcpy.Delete_management(Intermediate_Feature_Points_Projected)
        # add warning messages
        if not elevation_exists:
            arcpy.AddMessage("WARNING: Elevation not found. Zero elevations added.")
        arcpy.AddMessage("WARNING: NaN value(s) replaced with zero. Please check output for accuracy.")

        return
