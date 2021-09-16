# coding: utf-8

import scriptcontext as sc
from Rhino.Geometry import *
import ga_rotate3D

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
for j, axis in enumerate(axis_list):
    # Get scan mesh guid in doc
    ga_rotate.get_mesh_guid_by_layer("scan")

    # Set rotation axis
    ga_rotate.set_rotation_axis(axis)

    # 1. 初期集団を生成
    ga_rotate.generate_initial_population()

    for i in range(GENERATION):
        print("{0}世代".format(i + 1))

        # 2. 選択
        ga_rotate.selection()

        # 3. 交叉
        ga_rotate.crossover()

        # 4. 突然変異
        ga_rotate.mutate()

        # 集合に属する個体の情報を描画する
        ga_rotate.draw_population_info()

        # 変数の初期化
        ga_rotate.reset()

    # 5. Rotate scan mesh guid in doc after optimization
    ga_rotate.rotate_geometry_guid(index=j)

# Move timber to origin point
ga_rotate.move_timber_to_origin()


