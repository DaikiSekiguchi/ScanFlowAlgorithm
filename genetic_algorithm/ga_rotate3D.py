# coding: utf-8

import random
import copy
import rhinoscriptsyntax as rs
import scriptcontext
import Rhino
from Rhino.Geometry import *
import scriptcontext as sc
import math


class GA_rotate3D:
    # 初期化
    def __init__(self, gene_size, population_size, select_rate, mutate_rate):
        self.mesh_guid = None
        self.mesh = None
        self.axis = None

        self.gene_size = gene_size
        self.population_size = population_size
        self.select_rate = select_rate
        self.mutate_rate = mutate_rate

        self.population = []  # 集団
        self.individuals_fitness = []  # 集合に属する各個体の適応度
        self.selected_individuals = []  # 選択で残った適応度の高い個体群
        self.child_individuals = []  # 交叉、突然変異を経て新たに生成された個体群

    # 回転軸の設定
    def set_rotation_axis(self, axis):
        self.axis = axis

    # 1. 初期集団を生成する
    def generate_initial_population(self):
        self.population = []  # 集団

        for _ in range(self.population_size):
            # 個体(の遺伝子情報を格納するリスト)
            individual = []

            # ランダムに回転角度を設定し、個体の情報(遺伝子)を設定する
            for _ in range(self.gene_size):
                individual.append(random.uniform(0, 180))

            # 集団に個体を追加する
            self.population.append(individual)

    # 2. 指定した選択割合に基づき、適応度の高い個体を残す
    def selection(self):
        # 適応度を計算し、適応度が高い順に集団をソートする
        self.sort_fitness()

        # 残す個体の数を指定
        n = int(self.select_rate * self.population_size)

        for i in range(n):
            self.selected_individuals.append(copy.deepcopy(self.individuals_fitness[i][0]))

    # 集合の各個体の適応度を計算し、適応度が高い順にsortする
    def sort_fitness(self):
        # 各個体の適応度を計算する
        for individual in self.population:
            fitness_list = self.calc_fitness(individual)  # fitness(box height)が高い方が良い

            # Fitness of selected individual
            fitness = fitness_list[0]

            self.individuals_fitness.append([individual, fitness])

        # 適応度が高い順にソートする
        self.individuals_fitness.sort(key=lambda x: x[1], reverse=True)

    # 個体の適応度を計算する
    def calc_fitness(self, individual):

        fitness_list = []

        # Rotate geometry and calculate fitness(bounding box height)
        for i, gene_angle in enumerate(individual):
            # Rotate mesh (rotate angle is gene)
            gene_angle = math.radians(gene_angle)
            rotation_center = Point3d(0, 0, 0)
            self.rotate_geometry(gene_angle, rotation_center)

            # Bounding box around mesh geometry
            bounding_box = self.mesh.GetBoundingBox(True)

            # bounding box to Box
            box = Box(bounding_box)

            # Calc box height is fitness
            box_height = box.Z[1] - box.Z[0]  # fitness

            fitness_list.append(box_height)

        # Undo rotation
        for i, gene_angle in enumerate(individual):
            # Rotate mesh (rotate angle is gene)
            gene_angle = math.radians(gene_angle)
            rotation_center = Point3d(0, 0, 0)
            self.rotate_geometry(-gene_angle, rotation_center)

        return fitness_list

    # Geometryを回転させる
    def rotate_geometry(self, angle, rotation_center):
        xf = Transform.Rotation(angle, self.axis, rotation_center)  # 変位

        # プログラム(Rhino common)上の変数をここで更新する
        self.mesh.Transform(xf)  # scan mesh

    # Doc内の、Geometry Guidを回転させる
    def rotate_geometry_guid(self, guid_list=None, index=None):
        select_individual = self.population[0]
        gene_angle = math.radians(select_individual[0])
        rotation_center = Point3d(0, 0, 0)
        xf = Transform.Rotation(gene_angle, self.axis, rotation_center)  # 変位

        # プログラム(Rhino common)上の変数をここで更新する
        self.mesh.Transform(xf)  # scan mesh

        # モデル空間のGuidモデルに更新内容を反映させる
        if index >= 0:
            guid = scriptcontext.doc.Objects.Transform(self.mesh_guid, xf, False)

            if index == 0:
                rs.ObjectColor(guid, [255, 0, 0])
            elif index == 1:
                rs.ObjectColor(guid, [0, 255, 0])
            else:
                pass
        else:
            scriptcontext.doc.Objects.Transform(self.mesh_guid, xf, True)

        if guid_list:
            for g_list in guid_list:
                for guid in g_list:
                    scriptcontext.doc.Objects.Transform(guid, xf, True)

    # 3. 選択された適応度の高い個体群(集合)から任意に２個体を選択し、交叉させ、子を生成する
    def crossover(self):
        # 新しく生成する子(個体)の数
        num_crossover = self.population_size - len(self.selected_individuals)

        # 交叉を行う数だけ、子を生成する
        for i in range(num_crossover):
            parent_list = random.sample(self.selected_individuals, 2)  # 残った個体群から2つの個体を選択する(重複なし)

            parent1_gene = parent_list[0][0]  # parent1 rotate angle
            parent2_gene = parent_list[1][0]  # parent2 rotate angle

            # 子を生成
            child = [(parent1_gene + parent2_gene) / 2]

            # 子をリストに格納
            self.child_individuals.append(child)

    # 4. 一定の確率で突然変異させる
    def mutate(self):
        # for individual in self.child_individuals:
        #     for i in range(len(individual)):
        #         n = random.random()
        #         if n < self.mutate_rate:
        #             individual[i] = random.randint(0, 1)

        # 新しい集団 = 選択された個体群(親) + 新しく生成された個体群(子)
        self.selected_individuals.extend(self.child_individuals)
        self.population = copy.deepcopy(self.selected_individuals)

    # 集団に属する各個体の遺伝子情報を表示する
    def draw_population_info(self):
        for individual in self.individuals_fitness:
            print(individual)

    # 変数の初期化
    def reset(self):
        self.individuals_fitness = []
        self.selected_individuals = []
        self.child_individuals = []

    # Doc空間にあるscan dataをレイヤー情報から取得する
    def get_mesh_guid_by_layer(self, layer_name):
        original_scan_guid = sc.doc.Objects.FindByLayer(layer_name)

        for g in original_scan_guid:
            self.mesh_guid = g
            self.mesh = rs.coercemesh(self.mesh_guid)

            # self.mesh_guid = original_scan_guid[0]
            # self.mesh = rs.coercemesh(self.mesh_guid)

    def move_timber_to_origin(self, guid_list=None):

        # Get scan mesh guid in doc
        self.get_mesh_guid_by_layer("scan")

        # Bounding box around mesh geometry
        bounding_box = self.mesh.GetBoundingBox(True)

        # bounding box to Box
        box = Box(bounding_box)

        # Get from pt from box
        corner_pts = box.GetCorners()

        from_pt = Point3d(9999, 9999, 9999)
        for pt in corner_pts:
            if pt.Z < from_pt.Z:
                if pt.X < from_pt.X and pt.Y < from_pt.Y:
                    from_pt = pt

        # Translate timber
        origin_pt = Point3d(0, 0, -5)
        xf = Rhino.Geometry.Transform.Translation(Vector3d(origin_pt - from_pt))  # 変位

        # プログラム上の変数を更新
        self.mesh.Transform(xf)

        # モデル空間のGuidを移動させる
        scriptcontext.doc.Objects.Transform(self.mesh_guid, xf, True)  # scan mesh

        if guid_list:
            for g_list in guid_list:
                for guid in g_list:
                    scriptcontext.doc.Objects.Transform(guid, xf, True)  # arbitrary object guid

    def judge_up_and_down(self, orange_marker_guid, blue_marker_guid):

        # Get scan mesh guid in doc
        self.get_mesh_guid_by_layer("scan")

        # Bounding box around mesh geometry
        bounding_box = self.mesh.GetBoundingBox(True)

        # bounding box to Box
        box = Box(bounding_box)

        # Compare the z-coordinates of the two reference points
        orange_pt = rs.MeshAreaCentroid(orange_marker_guid[0])
        blue_pt = rs.MeshAreaCentroid(blue_marker_guid[0])

        # min_distance = 9999
        # blue_pt_guid = None
        #
        # for guid in blue_marker_guid:
        #     if guid == blue_pt_guid:
        #         pass
        #     else:
        #         another_mesh = rs.coercemesh(guid)
        #         temp_vertices = another_mesh.Vertices
        #         to_point = temp_vertices[0]  # arbitrary point on another meshes
        #
        #         # Distance reference pt to to_point
        #         distance = rs.Distance(orange_pt, to_point)
        #
        #         if distance < min_distance:
        #             min_distance = distance
        #             blue_pt_guid = guid
        #
        # print("Debug")
        #
        # blue_pt = rs.MeshAreaCentroid(blue_pt_guid)
        # print("Blue pt: {0}".format(blue_pt))
        # rs.AddPoint(blue_pt)
        # rs.AddLine(orange_pt, blue_pt)

        if orange_pt[2] > blue_pt[2]:
            print("Reverse")

            angle = math.radians(180)
            rotation_center = box.Center
            to_pt = Point3d(rotation_center.X + 100, rotation_center.Y, rotation_center.Z)
            self.axis = Vector3d(to_pt - rotation_center)

            # Rotate mesh object
            xf = Transform.Rotation(angle, self.axis, rotation_center)  # 変位

            # プログラム(Rhino common)上の変数をここで更新する
            self.mesh.Transform(xf)  # scan mesh

            # モデル空間のGuidモデルに更新内容を反映させる
            scriptcontext.doc.Objects.Transform(self.mesh_guid, xf, True)

            for guid in orange_marker_guid:
                scriptcontext.doc.Objects.Transform(guid, xf, True)

            for guid in blue_marker_guid:
                scriptcontext.doc.Objects.Transform(guid, xf, True)

            # Move bounding box to origin
            self.move_timber_to_origin([orange_marker_guid, blue_marker_guid])

