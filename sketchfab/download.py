# coding: utf-8

"""Sample script that shows how to list models, and various operations with them (comments,
collections...) using the V3 api and the requests library."""

import os
import json
import requests
from requests.exceptions import RequestException
import zipfile
import glob

SKETCHFAB_API_URL = 'https://api.sketchfab.com/v3'
API_TOKEN = 'c32d8c3d03894429a298943dd5829204'


def _get_request_payload(*, data=None, files=None, json_payload=False, isheader=False):
    """Helper method that returns the authentication token and proper content type depending on
    whether or not we use JSON payload."""
    data = data or {}
    files = files or {}

    if isheader:
        headers = {}
    else:
        headers = {'Authorization': 'Token {}'.format(API_TOKEN)}

    if json_payload:
        headers.update({'Content-Type': 'application/json'})
        data = json.dumps(data)

    return {'data': data, 'files': files, 'headers': headers}


def get_model_from_sketchfab(selected_model):
    get_model_urls = []

    my_models_endpoint = f'{SKETCHFAB_API_URL}/models/{selected_model["uid"]}/download'
    payload = _get_request_payload()  # payload: dict

    try:
        response = requests.get(my_models_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        data = response.json()

        # 3D scan format we can manipulate in sketchfab API
        gltf = data["gltf"]
        usdz = data["usdz"]

        gltf_url = gltf["url"]
        usdz_url = usdz["url"]

        # Model url is path to sketchfab api
        get_model_urls.append(gltf_url)
        get_model_urls.append(usdz_url)

        if not len(data) > 0:
            print('You don\'t seem to have any model :(')
        else:
            model_name = selected_model["name"]
            # get_model_from_sketchfab(model_name, get_model_urls)

            gltf_model_endpoint = get_model_urls[0]  # gltf (3D object format)
            usdz_model_endpoint = get_model_urls[1]  # usdz (3D object format)

            payload = _get_request_payload(isheader=True)  # payload: dict

            try:
                response = requests.get(gltf_model_endpoint, stream=True, **payload)
            except RequestException as exc:
                print(f'An API error occured: {exc}')
            else:
                print(response)

                timber_id = model_name

                # My local location to save model from sketchfab
                base_target_dir_original = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\01_original"
                base_target_dir_edit = r"G:\マイドライブ\2021\04_Master\2104_Scan\02_Timbers\02_edit"

                target_dir = os.path.join(base_target_dir_original, timber_id)
                file_path = os.path.join(target_dir, timber_id + ".zip")

                if not os.path.exists(target_dir):
                    os.mkdir(target_dir)

                # Make zip file
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                # extract zip file
                zip_file = zipfile.ZipFile(file_path)
                zip_file.extractall(target_dir)

                # Rename each file
                # files = glob.glob(os.path.join(target_dir, "*"))
                #
                # for file_path in files:
                #     if "scene.gltf" in file_path:
                #         new_file_name = os.path.join(target_dir, timber_id + ".gltf")
                #         os.rename(file_path, new_file_name)
                #
                #         print(file_path)
                #         print(new_file_name)
                #
                #     elif "scene.bin" in file_path:
                #         new_file_name = os.path.join(target_dir, timber_id + ".bin")
                #         os.rename(file_path, new_file_name)


def list_my_models():
    my_models_endpoint = f'{SKETCHFAB_API_URL}/me/models'  # url
    payload = _get_request_payload()  # payload: dict

    try:
        response = requests.get(my_models_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        data = response.json()

        if not len(data['results']) > 0:
            print('You don\'t seem to have any model :(')

        return data['results']


def get_collection():
    my_collections_endpoint = f'{SKETCHFAB_API_URL}/me/collections'
    payload = _get_request_payload()

    try:
        response = requests.get(my_collections_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
        exit(1)

    data = response.json()

    if not data['results']:
        print('You don\'t seem to have any collection, let\'s create one!')
        return
    else:
        return data['results'][1]


def create_collection(model):
    collections_endpoint = f'{SKETCHFAB_API_URL}/collections'
    data = {'name': 'Edited models', 'models': [model['uid']]}
    payload = _get_request_payload(data=data, json_payload=True)

    try:
        response = requests.post(collections_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        # We created our collection \o/
        # Now retrieve the data
        collection_url = response.headers['Location']
        response = requests.get(collection_url)

        return response.json()


def add_model_to_collection(model, collection):
    collection_model_endpoint = f'{SKETCHFAB_API_URL}/collections/{collection["uid"]}/models'

    payload = _get_request_payload(data={'models': [model['uid']]}, json_payload=True)
    try:
        response = requests.post(collection_model_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        if response.status_code == requests.codes.created:
            print(f'Model successfully added to collection {collection["uid"]}!')
        else:
            print('Model already in collection')


def remove_model_from_collection(model, collection):
    collection_model_endpoint = f'{SKETCHFAB_API_URL}/collections/{collection["uid"]}/models'

    payload = _get_request_payload(data={'models': [model['uid']]}, json_payload=True)
    try:
        response = requests.delete(collection_model_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        if response.status_code == requests.codes.no_content:
            print(f'Model successfully removed from collection {collection["uid"]}!')
        else:
            print(f'Model not in collection: {response.content}')


def comment_model(model, msg):
    comment_endpoint = f'{SKETCHFAB_API_URL}/comments'

    payload = _get_request_payload(data={'model': model['uid'], 'body': msg}, json_payload=True)
    try:
        response = requests.post(comment_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        if response.status_code == requests.codes.created:
            print('Comment successfully posted!')
        else:
            print(f'Failed to post the comment: {response.content}')


if __name__ == '__main__':
    result = get_collection()
    print(result)

    # Download
    print('Getting models from your profile...')

    # Timber'id which we try to get
    selected_timber_id = input("Input scan data name which you want to get (ex. Timber_001)" + "\n")

    # Timber which we try to get
    selected_model = None

    # All models in sketchfab
    models = list_my_models()

    # Extract model we want to get
    for model in models:
        if model["name"] == selected_timber_id:
            selected_model = model
            break

    # Get the timber scan model from sketchfab
    get_model_from_sketchfab(selected_model)

    print("The process all worked!")
