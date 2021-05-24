#!/usr/bin/python3

"""Sample script that shows how to update your profile and other social actions using the V3 api and
the requests library."""

import json
import random

# http://docs.python-requests.org/en/latest
# pip install requests
# import the requests library
import requests
from requests.exceptions import RequestException

SKETCHFAB_API_URL = 'https://api.sketchfab.com/v3'
API_TOKEN = 'c32d8c3d03894429a298943dd5829204'


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


def get_me():
    me_endpoint = f'{SKETCHFAB_API_URL}/me'
    payload = _get_request_payload()

    try:
        response = requests.get(me_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
        exit(1)
    else:
        return response.json()


def get_users():
    users_endpoint = f'{SKETCHFAB_API_URL}/users'
    payload = _get_request_payload()

    try:
        response = requests.get(users_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
        exit(1)
    else:
        return response.json()['results']


def follow_user(from_user, to_user):
    follow_endpoint = f'{SKETCHFAB_API_URL}/me/followings'
    payload = _get_request_payload(data={'toUser': to_user['uid']}, json_payload=True)

    try:
        response = requests.post(follow_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
        exit(1)
    else:
        if response.status_code == requests.codes.created:
            return True
        else:
            print('Already following this user!')
            return False


def unfollow_user(from_user, to_user):
    follow_endpoint = f'{SKETCHFAB_API_URL}/me/followings'
    payload = _get_request_payload(data={'toUser': to_user['uid']}, json_payload=True)

    try:
        response = requests.delete(follow_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
        exit(1)
    else:
        if response.status_code == requests.codes.no_content:
            return True
        else:
            print('Not following this user!')
            return False


def patch_profile(user, *, data):
    me_endpoint = f'{SKETCHFAB_API_URL}/me'
    payload = _get_request_payload(data=data, json_payload=True)

    try:
        response = requests.patch(me_endpoint, **payload)
    except RequestException as exc:
        print(f'An API error occured: {exc}')
    else:
        if response.status_code == requests.codes.no_content:
            print('Profile patched!')
            return True
        else:
            print(f'Could not patch your profile: {response.content}')

    return False


if __name__ == '__main__':
    # This requires that your profile contains at least one model
    print('Getting your profile...')

    me = get_me()
    print(type(me))

    with open("download.json", "w") as f:
        json.dump(me, f)

    # print(f'Hi {me["username"]}!')
    # print(
    #     'Now we\'ll patch your profile and update your tagline! '
    #     '(We\'ll revert that back afterwards)'
    # )
    #
    # old_tagline = me['tagline']
    #
    # if not patch_profile(me, data={'tagline': 'A new tagline'}):
    #     exit(1)
    #
    # if not patch_profile(me, data={'tagline': old_tagline}):
    #     print(f'Failed to reset your tagline to its previous value: {old_tagline}')
    #     exit(1)
    #
    # print('Done !')
    # print('Now we\'ll fetch some users and follow/unfollow one of them')
    #
    # users = get_users()
    #
    # user = users[random.randint(0, len(users))]
    #
    # follow_user(me, user)
    # print(f'You are now following {user["username"]}...')
    #
    # unfollow_user(me, user)
    # print('... Whom you just unfollowed :(')