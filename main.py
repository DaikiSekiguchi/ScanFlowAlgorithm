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

from export import export

# from .sketchfab import download, upload, profile

####################################################
# Get a scan data from sketch-fab.
# Convert a scan data which is mesh to Surface data.
####################################################

# Parameter
# Timber'id which we try to get
# selected_timber_id = rs.GetString("Input scan data name which you want to get (ex. Timber_001)")
selected_timber_id = "210904_timber1"

# Timber weight
timber_weight = rs.GetString("Input Timber weight (ex. 2.45(kg))")

# Import scan data from local environment
base_target_dir_original = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\01_original"
base_target_database_dir = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit\01_Database"
target_dir = os.path.join(base_target_dir_original, selected_timber_id)

# file_path = os.path.join(target_dir, "scene.gltf")  # scan data from sketchfab
file_path = os.path.join(target_dir, "model.obj")  # scan data from Trnio

if __name__ == '__main__':
    rs.EnableRedraw(False)

    ########################################################################################################
    # Get a scan data from sketch-fab
    ########################################################################################################

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
    # Import scan data and modify scan mesh data
    ########################################################################################################

    # Import scan data in Rhino
    rs.Command('_-Import {} _Enter'.format(file_path))

    # Get Scan Data which is mesh timber
    scan_mesh_timber = Timber.get_mesh_guid_in_doc()

    # Generate timber instance
    timber_instance = Timber(selected_timber_id, timber_weight, scan_mesh_timber)

    # join meshes which is imported
    timber_instance.join_each_meshes()

    # Adjusting the scale of an object
    timber_instance.scale_scan_mesh()

    # Rotate timber and move timber to origin coordinate(0, 0, 0)
    timber_instance.rotate_optimization_and_move_to_origin()

    # Delete not needed meshes to extract meshes of specific objects
    timber_instance.extract_timber_mesh()

    ########################################################################################################
    # Convert a scan data which is mesh to Surface data
    # 以下で取得するデータは、実環境上と情報環境上のスケールが一致するように、修正されたモノ
    ########################################################################################################

    # Mesh to Surface
    timber_instance.mesh_to_surface(250, 10)  # args(num_plane, interval_plane)

    # Export timber information
    upload_info = timber_instance.export_timber_information(base_target_database_dir, timber_instance)

    rs.UnselectAllObjects()

    rs.EnableRedraw(True)
