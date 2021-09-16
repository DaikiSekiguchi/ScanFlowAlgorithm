# coding: utf-8

import os
import qrcode
from sketchfab import download, upload, profile

if __name__ == "__main__":
    # Parameter
    SKETCHFAB_API_URL = 'https://api.sketchfab.com/v3'
    API_TOKEN = 'c32d8c3d03894429a298943dd5829204'
    MAX_RETRIES = 50
    MAX_ERRORS = 10
    RETRY_TIMEOUT = 5  # seconds

    ########################################################################################################
    # Upload scan timber model to sketchfab
    ########################################################################################################

    # Get timber id to upload
    timber_database_path = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit\01_Database\timber_database.csv"

    with open(timber_database_path) as f:
        timber_database_list = []
        for s_line in f:
            timber_data = [x.strip() for x in s_line.split(',') if not s_line == '']

            if len(timber_data) > 1:
                timber_database_list.append(timber_data)

        selected_timber_info = timber_database_list[-1]  # last added timber information
        selected_timber_folder_name = "ID" + selected_timber_info[0] + "_" + selected_timber_info[4]

    # Edited scan timber data path
    base_target_dir_edit = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit\01_Database"
    target_dir = os.path.join(base_target_dir_edit, selected_timber_folder_name, "OBJ")
    upload_file_path = os.path.join(target_dir, "mesh_timber" + "_" + selected_timber_folder_name + ".obj")

    # Upload in sketchfab
    model_url = upload.upload(upload_file_path, selected_timber_info)

    ########################################################################################################
    # Generate QR code and link QR code to sketchfab URL
    ########################################################################################################
    qr_dir = os.path.join(base_target_dir_edit, selected_timber_folder_name)
    qr_path = os.path.join(qr_dir, selected_timber_folder_name + ".png")

    img = qrcode.make(model_url)
    img.save(qr_path)
