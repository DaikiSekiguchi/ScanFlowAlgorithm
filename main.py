# coding: utf-8

import json
from time import sleep
import os
import sys
import time
import pickle
import importlib
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext
from timber import Timber

# from .sketchfab import download, upload, profile

####################################################
# Get a scan data from sketch-fab.
# Convert a scan data which is mesh to Surface data.
####################################################

if __name__ == '__main__':
    ########################################################################################################
    # Get a scan data from sketch-fab
    ########################################################################################################
    #
    # print('Getting models from your profile...')
    #
    # # Timber'id which we try to get
    selected_timber_id = "Timber_001"
    # selected_timber_id = input("Input scan data name which you want to get (ex. Timber_001)")
    #
    # # Timber which we try to get
    # selected_model = None
    #
    # # All models in sketchfab
    # models = download.list_my_models()
    #
    # # Extract model we want to get
    # for model in models:
    #     if model["name"] == selected_timber_id:
    #         selected_model = model
    #         break
    #
    # # Get the timber scan model from sketchfab
    # download.get_model_from_sketchfab(selected_model)

    ########################################################################################################
    # Convert a scan data which is mesh to Surface data
    ########################################################################################################

    # Import scan data from local environment
    base_target_dir_original = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\01_original"
    base_target_dir_edit = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit"

    target_dir = os.path.join(base_target_dir_original, selected_timber_id)
    file_path = os.path.join(target_dir, "scene.gltf")  # scan data

    # Import scan data in Rhino
    # rs.DocumentModified(False)
    # rs.Command('_-Open {} _Enter'.format(file_path))

    # join meshes which is imported
    # Timber.join_each_meshes()

    # Todo ここで、スケール合わせ、移動、メッシュ削除をする(現状はマニュアルでやっているが、自動化したい)
    # move timber to origin coordinate(0, 0, 0) and delete duplication and join some meshes to one mesh

    rs.EnableRedraw(False)

    # # 01. Get Scan Data which is mesh timber
    # # Todo ここで取得するデータは、実環境上と情報環境上のスケールが一致するように、修正されたモノ
    scan_mesh_timber = Timber.get_mesh_guid_in_doc()
    # scan_mesh_timber = rs.GetObject("Pick scan data", rs.filter.mesh)

    # 02. Generate timber instance
    timber_instance = Timber(selected_timber_id, scan_mesh_timber)

    # 03. Mesh to Surface
    timber_instance.mesh_to_surface(250, 10)  # args(num_plane, interval_plane)

    rs.EnableRedraw(True)

    # 04. Export timber information
    # Todo ここは editディレクトリにデータを保存する
    # Todo そして、editファイルをsketchfabに再度上げ直し、Draft Verのmodelはsketchfabから削除する
    # Todo Draftかどうかは、Tagなどで判定する？もしくはCollectionで、originalとTimberで分けて管理するか

    flag = "yes"
    # flag = rs.GetString("今回の生成データを保存しますか？ yes(y) or no(n)")

    if flag == "y" or flag == "yes":
        # Base target dir
        target_dir = os.path.join(base_target_dir_edit, selected_timber_id)  # ...\02_edit\Timber_id

        # Each file directory
        rhino_file_dir = os.path.join(target_dir, "Rhino")
        obj_file_dir = os.path.join(target_dir, "Obj")
        binary_file_dir = os.path.join(target_dir, "Binary-file")

        # Make the each file directory if it does't exist
        if not os.path.isdir(target_dir): os.mkdir(target_dir)
        if not os.path.isdir(rhino_file_dir): os.mkdir(rhino_file_dir)
        if not os.path.isdir(obj_file_dir): os.mkdir(obj_file_dir)
        if not os.path.isdir(binary_file_dir): os.mkdir(binary_file_dir)

        # Each file path
        rhino_file_path = os.path.join(rhino_file_dir, selected_timber_id + ".3dm")
        obj_file_path = os.path.join(obj_file_dir, selected_timber_id + ".obj")
        binary_file_path = os.path.join(binary_file_dir, selected_timber_id + ".binary")

        # Saving rhino(.3dm) file
        Timber.SaveAsRhinoFile(rhino_file_path)

        # Saving OBJ file

        rs.Command("_-Export " + obj_file_path + "_Enter")

        # Saving binary file
        with open(binary_file_path, "wb") as web:
            pickle.dump(timber_instance, web)

