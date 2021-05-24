# coding: utf-8

import rhinoscriptsyntax as rs
import scriptcontext
import Rhino
from Rhino.Geometry import *
import scriptcontext as sc


class Timber:

    def __init__(self, _id, _scan_mesh_timber):
        self.id = _id

        # About object(RhinoCommon)
        self.mesh_timber = rs.coercemesh(_scan_mesh_timber)
        self.srf_timber = None
        self.section_curves = []
        self.center_line = None

        # About guid
        self.scan_mesh_timber_guid = _scan_mesh_timber
        self.srf_timber_guid = None
        self.section_curves_guid = []
        self.center_line_guid = None

        # About layer
        self.parent_layer = None

    def create_timber_layer(self):

        # Parent layer of Timber instance
        self.parent_layer = Rhino.DocObjects.Layer()
        self.parent_layer.Name = self.id

        # Add parent layer in doc
        scriptcontext.doc.Layers.Add(self.parent_layer)

        # Create a child layer
        # parent_layer = self.parent_layer
        #
        # self.create_child_layer("mesh_timber", parent_layer)
        # self.create_child_layer("surface_timber", parent_layer)
        # self.create_child_layer("section_curves", parent_layer)
        # self.create_child_layer("center_line", parent_layer)

        # parent = rs.AddLayer(self.id, [0, 0, 0], True, False, None)
        # rs.AddLayer("mesh_timber", [0, 0, 0], True, False, parent)
        # rs.AddLayer("surface_timber", [0, 0, 0], True, False, parent)
        # rs.AddLayer("section_curves", [0, 0, 0], True, False, parent)
        # rs.AddLayer("center_line", [0, 0, 0], True, False, parent)

    @staticmethod
    def create_child_layer(child_name, parent_layer):
        child_layer = Rhino.DocObjects.Layer()
        child_layer.ParentLayerId = parent_layer.Id
        child_layer.Name = child_name

        # Add child layer in doc
        scriptcontext.doc.Layers.Add(child_layer)

    @staticmethod
    def get_mesh_guid_in_doc():
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
        rs.EnableRedraw(False)

        # Select duplication objs in doc and delete them
        rs.Command("_selDup")
        rs.Command("_Delete")

        doc_objs = sc.doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.Mesh)
        doc_objs = list(doc_objs)

        if len(doc_objs) >= 2:
            # Select each meshes and join them
            rs.Command("_selMesh")
            rs.Command("_join")
        else:
            pass

        rs.EnableRedraw(True)

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

    def mesh_to_surface(self, _num_plane, _interval_plane):
        mesh_planes = []
        section_curves = []

        # Add Layer
        self.create_timber_layer()

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

                section_curves.append(section_curve)

        # a = Rhino.Collections.CurveList(section_curves)
        # print(a)
        #
        # test = Brep.CreateFromLoftRebuild(a, Point3d.Unset, Point3d.Unset, LoftType.Tight, False, 20)
        # print(test)
        # for b in test:
        #     print(b)

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
        index = scriptcontext.doc.Layers.Find(self.id, True)
        parent_layer = scriptcontext.doc.Layers[index]

        self.create_child_layer("mesh_timber", parent_layer)
        self.create_child_layer("surface_timber", parent_layer)
        self.create_child_layer("section_curves", parent_layer)
        self.create_child_layer("center_line", parent_layer)

        # Assign object to layer
        rs.ObjectLayer(self.scan_mesh_timber_guid, "mesh_timber")
        rs.ObjectLayer(self.srf_timber_guid, "surface_timber")
        rs.ObjectLayer(self.section_curves_guid, "section_curves")
        rs.ObjectLayer(self.center_line_guid, "center_line")

        # Translate guid object to rhino common
        self.srf_timber = rs.coercebrep(self.srf_timber_guid)
        self.center_line = rs.coercecurve(self.center_line_guid)

        for section_crv_guid in self.section_curves_guid:
            section_crv = rs.coercecurve(section_crv_guid)
            self.section_curves.append(section_crv)

        rs.UnselectAllObjects()

        rs.EnableRedraw(False)

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
