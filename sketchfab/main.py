# coding: utf-8

import json
from time import sleep
import requests
from requests.exceptions import RequestException
import os
import sys
import time
import pickle
import importlib
import download, upload, profile

####################################################
# Get a scan data from sketch-fab.
####################################################

if __name__ == '__main__':
    print('Getting models from your profile...')

    # Timber'id which we try to get
    selected_timber_id = input("Input scan data name which you want to get (ex. Timber_001)" + "\n")

    # Timber which we try to get
    selected_model = None

    # All models in sketchfab
    models = download.list_my_models()

    # Extract model we want to get
    for model in models:
        if model["name"] == selected_timber_id:
            selected_model = model
            break

    # Get the timber scan model from sketchfab
    download.get_model_from_sketchfab(selected_model)

    print("The process all worked!")

