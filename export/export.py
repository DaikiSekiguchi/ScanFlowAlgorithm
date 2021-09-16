import scriptcontext
import rhinoscriptsyntax as rs


########################################################################################################
# this function via mcneel/rhinoscriptsyntax
# https://github.com/mcneel/rhinoscriptsyntax/blob/master/Scripts/rhinoscript/layer.py
########################################################################################################

def layerNames(select_layer_name, sort=False):
    rc = []
    for layer in scriptcontext.doc.Layers:
        if not layer.IsDeleted:
            if select_layer_name in str(layer):
                rc.append(layer.FullPath)

    if sort: rc.sort()

    return rc


def GetDAESettings():
    e_str = ""
    return e_str


def GetOBJSettings(geometry_type="NURBS"):
    # Select geometry type
    if geometry_type == "NURBS":
        # Save as NURBS
        e_str = "_Geometry=_NURBS "
        e_str += "_TrimCurves=Curves "

    elif geometry_type == "Mesh":
        # Save as Mesh model
        e_str = "_Geometry=_Mesh "

    else:
        # Save as NURBS
        e_str = "_Geometry=_NURBS "
        e_str += "_TrimCurves=Curves "

    e_str += "_EndOfLine=CRLF "
    e_str += "_ExportRhinoObjectNames=_ExportObjectsAsOBJGroups "
    e_str += "_ExportMeshTextureCoordinates=_Yes "
    e_str += "_ExportMeshVertexNormals=_No "
    e_str += "_CreateNGons=_No "
    e_str += "_ExportMaterialDefinitions=_No "
    e_str += "_YUp=_No "
    e_str += "_WrapLongLines=Yes "
    e_str += "_VertexWelding=_Welded "
    e_str += "_WritePrecision=16 "
    e_str += "_Enter "

    # e_str += "_DetailedOptions "
    # e_str += "_JaggedSeams=_No "
    # e_str += "_PackTextures=_No "
    # e_str += "_Refine=_Yes "
    # e_str += "_SimplePlane=_No "

    # e_str += "_AdvancedOptions "
    # e_str += "_Angle=50 "
    # e_str += "_AspectRatio=0 "
    # e_str += "_Distance=0.0"
    # e_str += "_Density=0 "
    # e_str += "_Density=0.45 "
    # e_str += "_Grid=0 "
    # e_str += "_MaxEdgeLength=0 "
    # e_str += "_MinEdgeLength=0.0001 "

    e_str += "_Enter _Enter"

    return e_str


def GetSTLSettings():
    eStr = "_ExportFileAs=_Binary "
    eStr += "_ExportUnfinishedObjects=_Yes "
    eStr += "_UseSimpleDialog=_No "
    eStr += "_UseSimpleParameters=_No "
    eStr += "_Enter _DetailedOptions "
    eStr += "_JaggedSeams=_No "
    eStr += "_PackTextures=_No "
    eStr += "_Refine=_Yes "
    eStr += "_SimplePlane=_No "
    eStr += "_AdvancedOptions "
    eStr += "_Angle=15 "
    eStr += "_AspectRatio=0 "
    eStr += "_Distance=0.01 "
    eStr += "_Grid=16 "
    eStr += "_MaxEdgeLength=0 "
    eStr += "_MinEdgeLength=0.0001 "
    eStr += "_Enter _Enter"
    return eStr


def export_object(selected_timber_id, obj_file_path, fileType="obj", visibleonly=False, byObject=False):
    # print("//export run started/////////////")

    # Settings
    settings_list = {
        'Get_DAE_Settings': GetDAESettings(),
        'Get_OBJ_NURBS_Settings': GetOBJSettings("NURBS"),
        'Get_OBJ_Mesh_Settings': GetOBJSettings("Mesh"),
        'Get_STL_Settings': GetSTLSettings(),
    }

    # File
    file_name = selected_timber_id + "." + fileType  # timber_id.fileType
    filePath = obj_file_path.rstrip(file_name)

    # Get all specific layers
    select_layer_name = "surface_timber"
    all_layers_path = layerNames(select_layer_name, False)

    # for layer in all_layers_path:
    #     print(layer)

    # initExport by layer
    init_export_by_layer(selected_timber_id, filePath, all_layers_path, settings_list, fileType, visibleonly, byObject)

    # print("//export run ended/////////////")


def init_export_by_layer(timber_id, filePath, layers, settings_list, fileType="obj", visibleonly=False, byObject=False):
    for layer_path in layers:
        layer = scriptcontext.doc.Layers.FindByFullPath(layer_path, True)

        # if layer exist
        if layer >= 0:
            layer = scriptcontext.doc.Layers[layer]  # layer path like 'Timber_001::mesh_timber'

            # Judge whether save or not
            save = True

            if visibleonly:
                if not layer.IsVisible:
                    save = False

            if rs.IsLayerEmpty(layer_path):
                save = False

            # If save flag is True
            if save:
                # Selected layer name
                layer_name = layer_path.split("::")
                layer_name = layer_name[len(layer_name) - 1]  # Name: surface_timber

                # Extract object in selected layer
                objs = scriptcontext.doc.Objects.FindByLayer(layer_name)

                # Save objects
                if len(objs) > 0:
                    if byObject:
                        i = 0
                        for obj in objs:
                            i = i + 1
                            save_objects_to_file(timber_id, filePath, settings_list, layer_name + "_" + str(i), [obj],
                                                 fileType)
                    else:
                        save_objects_to_file(timber_id, filePath, settings_list, layer_name, objs, fileType)


def save_objects_to_file(timber_id, filePath, settings_list, name, objs, fileType):
    rs.EnableRedraw(False)

    if len(objs) > 0:
        select_settings_list = []

        if fileType.upper() == "OBJ":
            settings_NURBS = settings_list["Get_" + fileType.upper() + "_NURBS" + "_Settings"]
            settings_Mesh = settings_list["Get_" + fileType.upper() + "_Mesh" + "_Settings"]
            select_settings_list.append(settings_NURBS)
            select_settings_list.append(settings_Mesh)

        else:
            settings = settings_list["Get_" + fileType.upper() + "_Settings"]
            select_settings_list.append(settings)

        rs.UnselectAllObjects()

        for obj in objs:
            obj.Select(True)

        for i, settings in enumerate(select_settings_list):
            # NURBS
            if i == 0:
                name = "".join(name.split(" "))
                name = name + "_" + timber_id

            # Mesh
            else:
                name = "mesh_timber" + "_" + timber_id

            command = '-_Export "{}{}{}" {}'.format(filePath, name, "." + fileType.lower(), settings)
            rs.Command(command, True)


if __name__ == '__main__':
    # init_export_by_layer("obj", True, False)
    # init_export_by_layer("dae", True, False)
    # init_export_by_layer("stl", True, False)

    pass
