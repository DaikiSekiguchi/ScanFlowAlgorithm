# coding: utf-8

import os
import rhinoscriptsyntax as rs
import scriptcontext
import Rhino
from Rhino.Geometry import *
import scriptcontext as sc
import math

import genetic_algorithm

reload(genetic_algorithm)

import genetic_algorithm.ga_rotate3D

reload(genetic_algorithm.ga_rotate3D)

from genetic_algorithm import ga_rotate3D
import pickle
import csv
from export import export


class Timber:

    def __init__(self, _id, _weight, _scan_mesh_timber):
        # About timber info
        self.id = "000"
        self.length = 0
        self.thickness = 0
        self.weight = _weight
        self.volume = None
        self.scan_date = _id

        # About object(RhinoCommon)
        self.original_scan_mesh = rs.coercemesh(_scan_mesh_timber)
        self.mesh_timber = None
        self.srf_timber = None
        self.section_curves = []
        self.center_line = None
        self.orange_marker_meshes = []
        self.blue_marker_meshes = []

        # About guid
        self.original_scan_mesh_guid = _scan_mesh_timber
        self.mesh_timber_guid = None
        self.srf_timber_guid = None
        self.section_curves_guid = []
        self.center_line_guid = None
        self.orange_marker_guid = []
        self.blue_marker_guid = []

        # About layer
        self.parent_layer = None

    def create_timber_layer(self, layer_name):

        # Parent layer of Timber instance
        self.parent_layer = Rhino.DocObjects.Layer()
        self.parent_layer.Name = layer_name

        # Add parent layer in doc
        scriptcontext.doc.Layers.Add(self.parent_layer)

    def restore_timber_instance(self):
        # Draw surface timber
        self.srf_timber_guid = scriptcontext.doc.Objects.AddBrep(self.srf_timber)
        rs.ObjectLayer(self.srf_timber_guid, "poly-surface")

        # Draw section curves
        for section_crv in self.section_curves:
            section_crv_guid = scriptcontext.doc.Objects.AddCurve(section_crv)
            rs.ObjectLayer(section_crv_guid, "section_curves")

            self.section_curves_guid.append(section_crv_guid)

        # Draw center line
        self.center_line_guid = scriptcontext.doc.Objects.AddCurve(self.center_line)
        rs.ObjectLayer(self.center_line_guid, "center_line")

    @staticmethod
    def create_child_layer(child_name, parent_layer):
        child_layer = Rhino.DocObjects.Layer()
        child_layer.ParentLayerId = parent_layer.Id
        child_layer.Name = child_name

        # Add child layer in doc
        scriptcontext.doc.Layers.Add(child_layer)

    @staticmethod
    def get_mesh_guid_in_doc():
        scriptcontext.doc = Rhino.RhinoDoc.ActiveDoc  # From GH

        obj_type = Rhino.DocObjects.ObjectType()
        obj_list = scriptcontext.doc.Objects.GetObjectList(obj_type)

        for obj in obj_list:
            if str(obj.ObjectType) == "Mesh":
                mesh_guid = obj.Id
                return mesh_guid

    @staticmethod
    def SaveAsRhinoFile(path):
        # filename = name
        # folder = "D:/Temp/"
        # path = os.path.abspath(folder + filename)
        cmd = "_-SaveAs " + chr(34) + path + chr(34)
        rs.Command(cmd, True)

    @staticmethod
    def join_each_meshes():
        rs.UnselectAllObjects()

        # Select duplication objs in doc and delete them
        rs.Command("_selDup")
        rs.Command("_Delete")

        doc_objs = sc.doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.Mesh)
        doc_objs = list(doc_objs)

        if len(doc_objs) >= 2:
            # Select each meshes and join them
            rs.Command("_selMesh")
            rs.Command("_join")

    def scale_scan_mesh(self):

        # Create scan mesh layer
        create_layer("scan")

        doc_objs = sc.doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.Mesh)
        doc_objs = list(doc_objs)
        # print("Number of doc objects: {}".format(len(doc_objs)))

        # Compute vertex color of meshes
        for obj in doc_objs:
            rs.UnselectAllObjects()

            # object layer
            rs.ObjectLayer(obj, "scan")

            # Select a mesh in doc
            sc.doc.Objects.Select(obj.Id)

            # Compute vertex color of selected mesh
            rs.Command("_ComputeVertexColors")

        # Marker meshes
        # mesh = None
        # mesh2 = None

        orange_mesh_list = []
        blue_mesh_list = []

        new_mesh_list_guid = []

        for obj in doc_objs:

            mesh1 = rs.coercemesh(obj)
            mesh2 = rs.coercemesh(obj)

            # Mesh variables
            color_list = mesh1.VertexColors

            faces_orange = mesh1.Faces
            faces_blue = mesh2.Faces

            # debug
            # print(type(faces[0]))
            # print("color list length: {0}".format(len(color_list)))
            # print("face list length: {0}".format(len(faces)))
            # print("vertex list length: {0}".format(len(vertices)))

            # Extract specific faces by using color information
            delete_faces_index_list_orange = []
            delete_faces_index_list_blue = []

            # process as many points as possible
            for i, face in enumerate(faces_orange):
                v1 = face.A  # vertex1 index
                v2 = face.B  # vertex2 index
                v3 = face.C  # vertex3 index

                # color list of a mesh vertexes
                temp_v_color_list = [color_list[v1], color_list[v2], color_list[v3]]

                # Average vertexes color
                # sum_R = (color_list[v1].R + color_list[v2].R + color_list[v3].R) / 3
                # sum_G = (color_list[v1].G + color_list[v2].G + color_list[v3].G) / 3
                # sum_B = (color_list[v1].B + color_list[v2].B + color_list[v3].B) / 3
                # print(sum_R, sum_G, sum_B)

                # Judge blue marker
                count = 0
                for v_color in temp_v_color_list:
                    if v_color.B >= v_color.G > v_color.R:
                        if (v_color.B > 200) and (v_color.R < 150):
                            if (10 < (abs(v_color.R - v_color.G)) < 90) and (0 < abs(v_color.G - v_color.B) < 70):
                                count = count + 1

                if count >= 2:
                    pass
                else:
                    delete_faces_index_list_blue.append(i)

                # Judge orange marker
                count = 0
                for v_color in temp_v_color_list:
                    # orange marker
                    # if (abs(v_color.R - v_color.G)) < 30 and (abs(v_color.G - v_color.B) > 40):
                    #     count = count + 1

                    # red marker
                    if (v_color.R > v_color.G) and (v_color.R > v_color.B):
                        if (abs(v_color.R - v_color.G)) > 40 and (abs(v_color.G - v_color.B) < 30):
                            count = count + 1

                if count >= 2:
                    pass
                else:
                    delete_faces_index_list_orange.append(i)

            # Delete specific faces from mesh
            faces_orange.DeleteFaces(delete_faces_index_list_orange)  # orange marker
            faces_blue.DeleteFaces(delete_faces_index_list_blue)  # blue marker

            orange_mesh_list.append(mesh1)
            blue_mesh_list.append(mesh2)

        # Create New guid mesh layer
        orange_marker_layer_name = "orange_marker"
        blue_marker_layer_name = "blue_marker"
        create_layer(orange_marker_layer_name)
        create_layer(blue_marker_layer_name)

        # Generate marker mesh Guid
        print(len(blue_mesh_list))
        print(len(orange_mesh_list))

        for mesh in blue_mesh_list:
            if mesh.IsValid:
                guid_blue_marker = scriptcontext.doc.Objects.AddMesh(mesh)
                rs.ObjectLayer(guid_blue_marker, blue_marker_layer_name)

        for mesh in orange_mesh_list:
            if mesh.IsValid:
                guid_orange_marker = scriptcontext.doc.Objects.AddMesh(mesh)
                rs.ObjectLayer(guid_orange_marker, orange_marker_layer_name)

        # Explode new meshes
        explode_objects(orange_marker_layer_name)
        explode_objects(blue_marker_layer_name)

        # Select the meshes having max area
        self.orange_marker_guid = select_max_area_obj(orange_marker_layer_name)
        self.blue_marker_guid = select_max_area_obj(blue_marker_layer_name)

        # Reset orange marker layer objects
        reset_layer_objs(orange_marker_layer_name, self.orange_marker_guid)
        reset_layer_objs(blue_marker_layer_name, self.blue_marker_guid)

        # original scan meshes guid
        original_guid = sc.doc.Objects.FindByLayer("scan")

        # Scale scan meshes guid to real timber scale
        scan_area = 0  # スキャンデータ上のマーカーの面積
        for guid in self.orange_marker_guid:
            area = rs.MeshArea(guid)
            scan_area += area[1]

        real_area = 50 * 50  # リアル環境のマーカーの面積
        print("scan marker meshes area: {0}".format(scan_area))
        print("real marker area: {0}".format(real_area))

        scale = real_area / scan_area  # 面積比
        scale = math.sqrt(scale)  # X軸、Y軸、(Z軸)スケールにスケール比を分解

        # Scan mesh guid
        rs.ScaleObject(original_guid, [0, 0, 0], [scale, scale, scale])

        # Orange marker mesh guid
        for guid in self.orange_marker_guid:
            rs.ScaleObject(guid, [0, 0, 0], [scale, scale, scale])

            # guid to RhinoCommon
            self.orange_marker_meshes.append(rs.coercemesh(guid))

        # Blue marker mesh guid
        for guid in self.blue_marker_guid:
            rs.ScaleObject(guid, [0, 0, 0], [scale, scale, scale])

            # guid to RhinoCommon
            self.blue_marker_meshes.append(rs.coercemesh(guid))

    def rotate_optimization_and_move_to_origin(self):

        # Parameter
        SELECT_RATE = 0.5  # 選択割合
        MUTATE_RATE = 0.1  # 突然変異の確立
        GENE_SIZE = 1  # 個体がもつ情報(回転角度)
        POPULATION_SIZE = 20  # 集団の個体数
        GENERATION = 5  # 世代数

        # インスタンスを生成
        ga_rotate = ga_rotate3D.GA_rotate3D(GENE_SIZE, POPULATION_SIZE, SELECT_RATE, MUTATE_RATE)

        # 回転軸の設定
        axis_list = [Vector3d(Point3d(1, 0, 0)), Vector3d(Point3d(0, 1, 0))]  # X-axis, Y-axis

        # Execute GA
        for axis in axis_list:
            # Get scan mesh guid in doc
            ga_rotate.get_mesh_guid_by_layer("scan")

            # Set rotation axis
            ga_rotate.set_rotation_axis(axis)

            # 1. 初期集団を生成
            ga_rotate.generate_initial_population()

            for i in range(GENERATION):
                # print("{0}世代".format(i + 1))

                # 2. 選択
                ga_rotate.selection()

                # 3. 交叉
                ga_rotate.crossover()

                # 4. 突然変異
                ga_rotate.mutate()

                # 集合に属する個体の情報を描画する
                # ga_rotate.draw_population_info()

                # 変数の初期化
                ga_rotate.reset()

            # 5. Rotate scan mesh guid in doc after optimization
            ga_rotate.rotate_geometry_guid([self.orange_marker_guid, self.blue_marker_guid])

        # Move timber to origin point
        ga_rotate.move_timber_to_origin([self.orange_marker_guid, self.blue_marker_guid])

        # Judge up and bottom of timber
        ga_rotate.judge_up_and_down(self.orange_marker_guid, self.blue_marker_guid)

    def extract_timber_mesh(self):
        # Only timber meshes
        mesh_timber = sc.doc.Objects.FindByLayer("scan")
        self.mesh_timber_guid = rs.CopyObject(mesh_timber[0].Id)

        # Only timber meshes(RhinoCommon)
        self.mesh_timber = rs.coercemesh(self.mesh_timber_guid)

        layer_blue_objs = sc.doc.Objects.FindByLayer("blue_marker")
        max_z_coordinate = -9999
        max_vertex = None

        min_z_coordinate = 9999
        min_vertex = None

        for guid in layer_blue_objs:
            mesh = rs.coercemesh(guid)

            vertices = mesh.Vertices

            for vertex in vertices:
                # Judge max z coordinate
                if vertex.Z > max_z_coordinate:
                    max_vertex = vertex
                    max_z_coordinate = vertex.Z

                # Judge min z coordinate
                if vertex.Z < min_z_coordinate:
                    min_vertex = vertex
                    min_z_coordinate = vertex.Z

        # debug
        rs.AddPoint(max_vertex)
        rs.AddPoint(min_vertex)

        # Reference point
        # reference_pt = [max_vertex.X, max_vertex.Y, max_vertex.Z]  # max z vertex
        reference_pt = [min_vertex.X, min_vertex.Y, min_vertex.Z]  # min z vertex

        # Split cutter
        width = 500
        depth = 500

        vertices = [
            [-width, -depth, reference_pt[2]],
            [-width, depth, reference_pt[2]],
            [width, depth, reference_pt[2]],
            [width, -depth, reference_pt[2]],
        ]

        faceVertices = [[0, 1, 2, 3]]
        cutter_mesh = rs.AddMesh(vertices, faceVertices)

        # Split timber mesh by cutting mesh
        re = rs.MeshBooleanSplit(self.mesh_timber_guid, cutter_mesh)

        # Get max area mesh from splitting mesh
        max_area_mesh = None
        max_area = -9999

        for guid in re:
            area = rs.MeshArea(guid)
            area = area[1]  # mesh area

            if area > max_area:
                max_area_mesh = guid
                max_area = area

        self.mesh_timber_guid = max_area_mesh
        self.mesh_timber = rs.coercemesh(self.mesh_timber_guid)

        for guid in re:
            if guid == self.mesh_timber_guid:
                pass
            else:
                rs.DeleteObject(guid)

        # # Generate bounding box
        # reference_pt = rs.MeshAreaCentroid(self.orange_marker_guid[0])
        # # rs.AddPoint(reference_pt)
        #
        # width = 200
        # depth = 200
        # height1 = 220
        # height2 = 1300
        #
        # corners = [
        #     Point3d(-width, -depth, -height1),
        #     Point3d(-width, depth, -height1),
        #     Point3d(width, depth, -height1),
        #     Point3d(width, -depth, -height1),
        #     Point3d(-width, -depth, height2),
        #     Point3d(-width, depth, height2),
        #     Point3d(width, depth, height2),
        #     Point3d(width, -depth, height2),
        # ]
        #
        # for i, pt in enumerate(corners):
        #     corners[i] = pt + reference_pt

        # rs.AddBox(corners)

    def mesh_to_surface(self, _num_plane, _interval_plane):
        mesh_planes = []
        section_curves = []

        # Add Layer
        self.create_timber_layer(self.scan_date)

        # Generate mesh plane to get section curve
        for i in range(_num_plane):
            # Mesh Instance
            mesh_plane = Mesh()

            # Vertices of mesh
            mesh_plane.Vertices.Add(Point3d(-5000, -5000, i * _interval_plane))
            mesh_plane.Vertices.Add(Point3d(-5000, 5000, i * _interval_plane))
            mesh_plane.Vertices.Add(Point3d(5000, 5000, i * _interval_plane))
            mesh_plane.Vertices.Add(Point3d(5000, -5000, i * _interval_plane))

            # Faces of mesh
            mesh_plane.Faces.AddFace(0, 1, 2, 3)

            # Generate Mesh
            mesh_plane.Normals.ComputeNormals()
            mesh_plane.Compact()

            # Maintain mesh plane
            mesh_planes.append(mesh_plane)

        # Intersect mesh timber and mesh planes
        for mesh_plane in mesh_planes:
            output = Intersect.Intersection.MeshMeshAccurate(self.mesh_timber, mesh_plane, 0.0000001)

            if output:
                # Extract section curve
                section_curve = output[0]

                # Polyline to Curve
                section_curve = section_curve.ToNurbsCurve()

                # Rebuild Curve
                # section_curve.Rebuild(50, 3, False)

                # Judge curve length
                length = rs.CurveLength(section_curve)
                if length < 100:
                    pass
                else:
                    section_curves.append(section_curve)

        ################################################################
        # Extract some section curves on timber
        # temp_crv_length_list = []
        # for crv in section_curves:
        #     length = rs.CurveLength(crv)
        #     temp_crv_length_list.append(length)
        #
        # index = temp_crv_length_list.index(min(temp_crv_length_list))
        # print("min crv len: {0}".format(temp_crv_length_list[index]))
        # section_curves = section_curves[:index]
        ################################################################

        # Draw closed section curves in RhinoDoc
        for crv in section_curves:
            if crv.IsClosed:
                self.section_curves_guid.append(scriptcontext.doc.Objects.AddCurve(crv))
            else:
                # Ignore open curve
                pass

        # Rebuild section curves -> ここでリビルドしないとLoftがうまくいかないため
        rs.Command("_selclosedcrv")
        rs.Command('_RebuildCrvNonUniform _Enter')

        # Seam crv -> ここでseamしないとLoftがうまくいかないため
        rs.Command("_selclosedcrv")
        rs.Command('_crvseam _Enter')

        # Generate poly-surface timber by using Loft command
        self.create_loft_surface()

        # Generate center line from centroid of section curves
        centroids = []

        for crv in self.section_curves_guid:
            out = rs.CurveAreaCentroid(crv)
            centroids.append(out[0])

        self.center_line_guid = rs.AddPolyline(centroids)

        # Create child layer
        index = scriptcontext.doc.Layers.Find(self.scan_date, True)
        parent_layer = scriptcontext.doc.Layers[index]
        self.create_child_layer("original_scan_mesh", parent_layer)
        self.create_child_layer("timber_mesh", parent_layer)
        self.create_child_layer("surface_timber", parent_layer)
        self.create_child_layer("section_curves", parent_layer)
        self.create_child_layer("center_line", parent_layer)

        # Assign object to layer
        rs.ObjectLayer(self.original_scan_mesh_guid, "original_scan_mesh")
        rs.ObjectLayer(self.mesh_timber_guid, "timber_mesh")
        rs.ObjectLayer(self.srf_timber_guid, "surface_timber")
        rs.ObjectLayer(self.section_curves_guid, "section_curves")
        rs.ObjectLayer(self.center_line_guid, "center_line")

        # Translate guid object to rhino common
        self.srf_timber = rs.coercebrep(self.srf_timber_guid)
        self.center_line = rs.coercecurve(self.center_line_guid)

        for section_crv_guid in self.section_curves_guid:
            section_crv = rs.coercecurve(section_crv_guid)
            self.section_curves.append(section_crv)

        # Set timber info
        # timber length
        start_pt = self.center_line.PointAtStart
        end_pt = self.center_line.PointAtEnd
        self.length = start_pt.DistanceTo(end_pt)
        print(self.length)

        self.length = int(math.floor(self.length))
        print(self.length)

        # average timber thickness
        sum_length = 0
        for section_crv in self.section_curves:
            sum_length += rs.CurveLength(section_crv)

        self.thickness = (sum_length / len(self.section_curves)) / math.pi
        self.thickness = int(math.floor(self.thickness))

        # Volume of timber
        self.volume = rs.SurfaceVolume(self.srf_timber_guid)
        print(self.volume)

        self.volume = self.volume[0] / 10 ** 9
        print(self.volume)

    def create_loft_surface(self):
        temp_sort_crv_list = []
        sort_crv_list = []

        # Extract z coordinate of point which is on section curve
        for crv in self.section_curves_guid:
            domain = rs.CurveDomain(crv)
            parameter = (domain[0] + domain[1]) / 2.0

            point = rs.EvaluateCurve(crv, parameter)
            z_coordinate = point[2]

            # Seam crv
            # rs.CurveSeam(crv, parameter)

            temp_sort_crv_list.append([crv, z_coordinate])

        # Sort list by z coordinate
        temp_sort_crv_list = sorted(temp_sort_crv_list, reverse=False, key=lambda x: x[1])

        # Extract only curve
        for crv_info in temp_sort_crv_list:
            sort_crv_list.append(crv_info[0])

        # Create Loft Surface
        self.srf_timber_guid = rs.AddLoftSrf(sort_crv_list, None, None, 3, 1, 50, False)

        # Caps planar holes in Loft Surface
        rs.CapPlanarHoles(self.srf_timber_guid)

    def export_timber_information(self, base_target_database_dir, timber_instance):
        # Todo ここは editディレクトリにデータを保存する
        # Todo そして、editファイルをsketchfabに再度上げ直し、Draft Verのmodelはsketchfabから削除する
        # Todo Draftかどうかは、Tagなどで判定する？もしくはCollectionで、originalとTimberで分けて管理するか

        # Timber csv database path 
        path_to_csv_database = os.path.join(base_target_database_dir, ("timber_database" + ".csv"))

        # Calc data length in scan database
        with open(path_to_csv_database) as f:
            next(csv.reader(f))  # skip header
            reader = csv.reader(f)

            scan_ids = []
            for row in reader:
                if row:
                    scan_ids.append(row[4])

            data_length = len(scan_ids)

        # Update Timber id
        self.id = str(data_length + 1)

        # Folder name
        folder_name = "ID" + self.id + "_" + self.scan_date

        # Base target folder dir
        target_dir = os.path.join(base_target_database_dir, folder_name)  # ...\02_edit\01_database\target dir

        # Each file folder directory
        rhino_file_dir = os.path.join(target_dir, "Rhino")
        obj_file_dir = os.path.join(target_dir, "OBJ")
        binary_file_dir = os.path.join(target_dir, "BinaryFile")

        # Make the each file directory if it does't exist
        if not os.path.isdir(rhino_file_dir): os.mkdir(rhino_file_dir)
        if not os.path.isdir(obj_file_dir): os.mkdir(obj_file_dir)
        if not os.path.isdir(binary_file_dir): os.mkdir(binary_file_dir)

        # Each file path
        rhino_file_path = os.path.join(rhino_file_dir, folder_name + ".3dm")
        obj_file_path = os.path.join(obj_file_dir, folder_name + ".obj")
        binary_file_path = os.path.join(binary_file_dir, folder_name + ".binary")
        qr_code_file_path = os.path.join(target_dir, "Timber_" + self.id + ".png")

        # Save Rhino(.3dm) file
        Timber.SaveAsRhinoFile(rhino_file_path)

        # Save OBJ file(Mesh or NURBS)
        export.export_object(folder_name, obj_file_path, "obj", True, False)

        # Save binary file
        with open(binary_file_path, "wb") as web:
            pickle.dump(timber_instance, web)

        # Write new scan timber info in database
        with open(path_to_csv_database, "a") as csv_file:
            writer = csv.writer(csv_file, lineterminator="\n")

            writing_info = [self.id, self.length, self.thickness, self.weight, self.scan_date,
                            target_dir.encode("utf-8"), qr_code_file_path.encode("utf-8")]
            writer.writerow(writing_info)

        # Get description about timber
        title = "Timber_" + self.id
        description = get_description_of_timber(writing_info)
        tags = "trnio 3dscan"
        isPublished = False

        output = [self.srf_timber_guid, target_dir, title, description, tags, isPublished]

        return output

    @staticmethod
    def judge_already_scan_or_not(timber_id):
        path_to_csv_database = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit\01_Database\timber_database.csv"

        # Make file if it does't exist
        if not os.path.isfile(path_to_csv_database):
            with open(path_to_csv_database, "w") as csv_file:
                writer = csv.writer(csv_file, lineterminator="\n")

                # Write header
                writer.writerow(["id", "length", "thickness", "weight", "date", "path", "qr_path"])

        # Calc data length in scan database
        with open(path_to_csv_database) as f:
            next(csv.reader(f))  # skip header
            reader = csv.reader(f)

            scan_ids = []
            for row in reader:
                if row:
                    scan_ids.append(row[4])

        # Judge already scan or not
        if timber_id in scan_ids:
            print("{0} is already scan".format(timber_id))
            return False
        else:
            return True


def get_description_of_timber(timber_info):
    timber_id = timber_info[0]
    length = timber_info[1]
    average_thickness = timber_info[2]
    weight = timber_info[3]
    split_data = timber_info[4].split("_")
    scan_date = split_data[0]

    description = "Timber ID: {0}".format(timber_id) + " / " + "Length: {0}mm".format(length) + " / " \
                  + "Average Thickness: {0}mm".format(average_thickness) + " / " \
                  + "Weight: {0}kg".format(weight) + " / " + "Scan Date: {0}".format(scan_date)

    return description


def create_layer(layer_name):
    # Parent layer of Timber instance
    parent_layer = Rhino.DocObjects.Layer()
    parent_layer.Name = layer_name

    # Add parent layer in doc
    scriptcontext.doc.Layers.Add(parent_layer)


def explode_objects(layer_name):
    exploded_meshes = []
    layer_objs = sc.doc.Objects.FindByLayer(layer_name)

    for guid in layer_objs:
        exploded_meshes.append(rs.ExplodeMeshes(guid, True))

    for mesh in exploded_meshes:
        rs.ObjectLayer(mesh, layer_name)


def select_max_area_obj(layer_name, reference_pt=None):
    layer_objs_guid = sc.doc.Objects.FindByLayer(layer_name)  # maybe this meshes including some trash meshes

    if reference_pt:
        orange_pt = rs.MeshAreaCentroid(reference_pt[0])

        min_distance = 9999
        select_guid_mesh = None

        for guid in layer_objs_guid:
            if guid == select_guid_mesh:
                pass
            else:
                another_mesh = rs.coercemesh(guid)
                temp_vertices = another_mesh.Vertices
                to_point = temp_vertices[0]  # arbitrary point on another meshes

                # Distance reference pt to to_point
                distance = rs.Distance(orange_pt, to_point)

                if distance < min_distance:
                    min_distance = distance
                    select_guid_mesh = guid

    else:
        select_guid_mesh = None
        max_area = -9999

        for guid in layer_objs_guid:
            area = rs.MeshArea(guid)

            if area[1] > max_area:
                max_area = area[1]
                select_guid_mesh = guid

    # Search marker mesh from max area meshes
    selected_mesh = rs.coercemesh(select_guid_mesh)

    vertices = selected_mesh.Vertices
    reference_pt = vertices[0]  # arbitrary point on meshes having max area

    marker_guid_mesh_list = [select_guid_mesh.Id]  # Object guid ID

    for guid in layer_objs_guid:
        if guid == select_guid_mesh:
            pass
        else:
            another_mesh = rs.coercemesh(guid)
            temp_vertices = another_mesh.Vertices
            to_point = temp_vertices[0]  # arbitrary point on another meshes

            # Distance reference pt to to_point
            distance = rs.Distance(reference_pt, to_point)

            if distance < 0.3:
                marker_guid_mesh_list.append(guid.Id)

    return marker_guid_mesh_list


def reset_layer_objs(layer_name, check_guid_list):
    layer_objs = sc.doc.Objects.FindByLayer(layer_name)

    for guid in layer_objs:
        if guid.Id in check_guid_list:
            pass
        else:
            rs.DeleteObject(guid)
