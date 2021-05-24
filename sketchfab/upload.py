#!/usr/bin/python3

"""Sample script for uploading to Sketchfab using the V3 API and the requests library."""

import json
from time import sleep

# import the requests library
# http://docs.python-requests.org/en/latest
# pip install requests
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
API_TOKEN = 'c32d8c3d03894429a298943dd5829204'
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


def upload():
    """
    POST a model to sketchfab.
    This endpoint only accepts formData as we upload a file.
    """
    model_endpoint = f'{SKETCHFAB_API_URL}/models'  # model url in sketchfab

    # Mandatory parameters
    model_file = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\01_original\210516_timber1\Timber_001_mesh_edit.obj"

    # Optional parameters
    data = {
        'name': 'Timber_model',
        'description': 'This is a timber model',
        'tags': ['trnio', '3dscan'],  # Array of tags,
        'categories': [],  # Array of categories slugs,
        'license': 'CC Attribution',  # License label,
        # 'private': 0,  # requires a pro account,
        # 'password': 'my-password',  # requires a pro account,
        'isPublished': True,  # Model will be on draft instead of published,
        'isInspectable': True,  # Allow 2D view in model inspector
        'length': 1000,
    }

    print('Uploading...')

    with open(model_file, 'rb') as file_:
        files = {'modelFile': file_}  # open file
        payload = _get_request_payload(data=data, files=files)

        # try to register some information with the server
        try:
            response = requests.post(model_endpoint, **payload)  # requests.post(URL, arbitrary args)
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
    a = 10
    model_url = upload()  # get model url(like https://api.sketchfab.com/v3/models/919a98941c82443fbbd2f027fc96ad6a)

    # if model_url:
    #     if poll_processing_status(model_url):
    #         patch_model(model_url)
    #         patch_model_options(model_url)