# coding: utf-8

"""Sample script for uploading to Sketchfab using the V3 API and the requests library."""

import json
from time import sleep
import os
from math import floor
import glob
import urllib2
import requests
from requests.exceptions import RequestException

##
# Uploading a model to Sketchfab is a two step process
#
# 1. Upload a model. If the upload is successful, the API will return
#    the model's uid in the `Location` header, and the model will be placed in the processing queue
#
# 2. Poll for the processing status
#    You can use your model id (see 1.) to poll the model processing status
#    The processing status can be one of the following:
#    - PENDING: the model is in the processing queue
#    - PROCESSING: the model is being processed
#    - SUCCESSED: the model has being sucessfully processed and can be view on sketchfab.com
#    - FAILED: the processing has failed. An error message detailing the reason for the failure
#              will be returned with the response
#
# HINTS
# - limit the rate at which you poll for the status (once every few seconds is more than enough)
##

SKETCHFAB_API_URL = 'https://api.sketchfab.com/v3'
API_TOKEN = ''
MAX_RETRIES = 50
MAX_ERRORS = 10
RETRY_TIMEOUT = 5  # seconds


def _get_request_payload(*, data=None, files=None, json_payload=False):
    """Helper method that returns the authentication token and proper content type depending on
    whether or not we use JSON payload."""
    data = data or {}
    files = files or {}
    headers = {'Authorization': f'Token {API_TOKEN}'}

    if json_payload:
        headers.update({'Content-Type': 'application/json'})
        data = json.dumps(data)

    return {'data': data, 'files': files, 'headers': headers}


def upload(select_model_file, timber_info=None):
    """
    POST a model to sketchfab.
    This endpoint only accepts formData as we upload a file.
    """
    model_endpoint = f'{SKETCHFAB_API_URL}/models'  # model url in sketchfab

    # Timber information
    timber_id = timber_info[0]

    length = timber_info[1]
    print(length)
    length = timber_info[1].split(".")
    length = length[0]
    print(length)

    average_thickness = timber_info[2]
    # average_thickness = timber_info[2].split(".")
    # average_thickness = average_thickness[0]

    weight = timber_info[3]
    split = timber_info[4].split("_")
    scan_date = split[0]

    description = "Timber ID: {0}".format(timber_id) + " / " + "Length: {0}mm".format(length) + " / " \
                  + "Average Thickness: {0}mm".format(average_thickness) + " / " \
                  + "Weight: {0}kg".format(weight) + " / " + "Scan Date: {0}".format(scan_date)

    print(description)

    # Optional parameters
    data = {
        'name': "Timber " + timber_id,
        'description': description,
        'tags': ['trnio', '3dscan'],  # Array of tags,
        'categories': [],  # Array of categories slugs,
        'license': 'CC Attribution',  # License label,
        # 'private': 0,  # requires a pro account,
        # 'password': 'my-password',  # requires a pro account,
        'isPublished': True,  # Model will be on draft instead of published,
        'isInspectable': True,  # Allow 2D view in model inspector
    }

    print('Uploading...')

    with open(select_model_file, 'rb') as file_:
        files = {'modelFile': file_}  # open file
        payload = _get_request_payload(data=data, files=files)

        # try to register some information with the server
        try:
            # urllib2 -> 2系
            response = urllib2.Request(model_endpoint, **payload)

            # requests module
            # response = requests.post(model_endpoint, **payload)  # requests.post(URL, arbitrary args)
        except RequestException as exc:
            print(f'An error occured: {exc}')
            return

    print(response)

    if response.status_code != requests.codes.created:
        print(f'Upload failed with error: {response.json()}')
        return

    # Should be https://api.sketchfab.com/v3/models/XXXX
    model_url = response.headers['Location']
    print('Upload successful. Your model is being processed.')
    print(f'Once the processing is done, the model will be available at: {model_url}')

    return model_url


def poll_processing_status(model_url):
    """GET the model endpoint to check the processing status."""
    errors = 0
    retry = 0

    print('Start polling processing status for model')

    while (retry < MAX_RETRIES) and (errors < MAX_ERRORS):
        print(f'Try polling processing status (attempt #{retry})...')

        payload = _get_request_payload()

        try:
            response = requests.get(model_url, **payload)
        except RequestException as exc:
            print(f'Try failed with error {exc}')
            errors += 1
            retry += 1
            continue

        result = response.json()

        if response.status_code != requests.codes.ok:
            print(f'Upload failed with error: {result["error"]}')
            errors += 1
            retry += 1
            continue

        processing_status = result['status']['processing']

        if processing_status == 'PENDING':
            print(f'Your model is in the processing queue. Will retry in {RETRY_TIMEOUT} seconds')
            retry += 1
            sleep(RETRY_TIMEOUT)
            continue
        elif processing_status == 'PROCESSING':
            print(f'Your model is still being processed. Will retry in {RETRY_TIMEOUT} seconds')
            retry += 1
            sleep(RETRY_TIMEOUT)
            continue
        elif processing_status == 'FAILED':
            print(f'Processing failed: {result["error"]}')
            return False
        elif processing_status == 'SUCCEEDED':
            print(f'Processing successful. Check your model here: {model_url}')
            return True

        retry += 1

    print('Stopped polling after too many retries or too many errors')
    return False


def patch_model(model_url):
    """
    PATCH the model endpoint to update its name, description...
    Important: The call uses a JSON payload.
    """

    payload = _get_request_payload(data={'name': 'A super Bob model'}, json_payload=True)

    try:
        response = requests.patch(model_url, **payload)
    except RequestException as exc:
        print(f'An error occured: {exc}')
    else:
        if response.status_code == requests.codes.no_content:
            print('PATCH model successful.')
        else:
            print(f'PATCH model failed with error: {response.content}')


def patch_model_options(model_url):
    """PATCH the model options endpoint to update the model background, shading, orienration."""
    data = {
        'shading': 'shadeless',
        'background': '{"color": "#FFFFFF"}',
        # For axis/angle rotation:
        'orientation': '{"axis": [1, 1, 0], "angle": 34}',
        # Or for 4x4 matrix rotation:
        # 'orientation': '{"matrix": [1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]}'
    }
    payload = _get_request_payload(data=data, json_payload=True)
    try:
        response = requests.patch(f'{model_url}/options', **payload)
    except RequestException as exc:
        print(f'An error occured: {exc}')
    else:
        if response.status_code == requests.codes.no_content:
            print('PATCH options successful.')
        else:
            print(f'PATCH options failed with error: {response.content}')


###################################
# Uploads, polls and patch a model
###################################

if __name__ == '__main__':
    # Timber'id which we try to get
    selected_timber_id = input("Input timber data name which you want to upload in sketchfab (ex. Timber_001)" + "\n")

    # edited scan timber data by RhinoPython
    base_target_dir_edit = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit\01_Database"
    target_dir = os.path.join(base_target_dir_edit, selected_timber_id, "OBJ")
    upload_file_path = os.path.join(target_dir, "mesh_timber" + "_" + selected_timber_id + ".obj")

    # Extract upload model file
    # files = glob.glob(os.path.join(target_dir, "*"))
    #
    # for file in files:
    #     if "mesh_timber" in file and selected_timber_id in file:
    #         print(file)
    #         upload_file_path = file
    #     else:
    #         pass

    # Upload in sketchfab
    select_model_url = upload(upload_file_path, selected_timber_id)

    # if model_url:
    #     if poll_processing_status(model_url):
    #         patch_model(model_url)
    #         patch_model_options(model_url)
