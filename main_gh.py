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

import timber

reload(timber)
from timber import Timber

if flag:
    # judge already scan or not
    result = Timber.judge_already_scan_or_not(selected_timber_id)

    if result:

        # Timber weight
        timber_weight = rs.GetString("Input Timber weight (ex. 2.43(kg))")

        # Scan folder path
        base_target_dir_original = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\01_original"
        base_target_database_dir = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit\01_Database"
        target_dir = os.path.join(base_target_dir_original, selected_timber_id)

        # file_path = os.path.join(target_dir, "scene.gltf")  # scan data from sketchfab
        file_path = os.path.join(target_dir, "model.obj")  # scan data from Trnio

        rs.EnableRedraw(False)

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
        ########################################################################################################

        # Mesh to Surface
        timber_instance.mesh_to_surface(250, 10)  # args(num_plane, interval_plane)

        # Export timber information
        upload_info = timber_instance.export_timber_information(base_target_database_dir, timber_instance)

        if upload_info:
            # Output in grasshopper
            geometry = upload_info[0]
            target_dir = upload_info[1]
            title = upload_info[2]
            description = upload_info[3]
            tags = upload_info[4]
            isPublished = upload_info[5]

        rs.UnselectAllObjects()

        rs.EnableRedraw(True)
