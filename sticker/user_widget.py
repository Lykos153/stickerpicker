#!/usr/bin/env python3

import datetime
import requests
import os
import argparse

def get_users(homeserver, admin_token):
    next_token = 0
    while True:
        jret = requests.get(
            f"{homeserver}/_synapse/admin/v2/users",
            # headers = header,
            params= {
                "access_token": admin_token,
                "from": next_token,
                "limit": 10,
                "guests": "true"
            }
        ).json()
        for user in jret['users']:
            yield user['name']
        if 'next_token' in jret:
            next_token = jret['next_token']
        else:
            return

def get_login_token(homeserver, user, admin_token):
    expire_at = datetime.datetime.now() + datetime.timedelta(days=1)
    res = requests.post(
        f"{homeserver}/_synapse/admin/v1/users/{user}/login",
        params={'access_token': admin_token},
        json={'valid_until_ms': int(expire_at.timestamp()*1000)}
    )
    try:
        token = res.json()['access_token']
    except KeyError:
        raise Exception(f"Could not get token for {user}", res.json())
    else:
        return token

def get_m_widgets(homeserver, user, token):
    res = requests.get(
        f"{homeserver}/_matrix/client/v3/user/{user}/account_data/m.widgets",
        params={'access_token': token}
    )
    return res.json()

def set_m_widgets(homeserver, user, token, url, erase=False):

    account_widgets = get_m_widgets(homeserver, user, token)
    if erase:
        account_widgets = {}
    account_widgets['stickerpicker'] = \
    {
        "content": {
            "type": "m.stickerpicker",
            "url": url,
            "name": "Stickerpicker",
            "data": {}
        },
        "sender": user,
        "state_key": "stickerpicker",
        "type": "m.widget",
        "id": "stickerpicker"
    }
    res = requests.put(
        f"{homeserver}/_matrix/client/v3/user/{user}/account_data/m.widgets",
        params={'access_token': token},
        json = account_widgets
    )
    return res.status_code == 200

def set_m_widgets_users(homeserver, users, admin_token, sticker_url, erase=False):
    print(f"Setting widgets...")
    for user in users:
        print(f"  {user}")
        token = get_login_token(homeserver, user, admin_token)
        set_m_widgets(homeserver, user, token, sticker_url, erase=erase)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "user",
        help="User(s) for whom to enable the stickerpicker widget",
        nargs="*"
    )

    parser.add_argument("--url", help="URL to the stickerpicker", default="https://maunium.net/stickers-demo/?theme=$theme")
    
    args = parser.parse_args()

    admin_token = os.environ["MATRIX_ADMIN_TOKEN"]
    homeserver = os.environ["MATRIX_HOMESERVER"]

    set_m_widgets_users(homeserver, args.user, admin_token, args.url)
