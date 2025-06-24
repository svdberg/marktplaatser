import os

if os.environ.get("IS_LOCAL"):
    from dotenv import load_dotenv
    load_dotenv()

import requests


def get_marktplaats_access_token():
    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(
        "https://auth.marktplaats.nl/accounts/oauth/token", headers=headers, data=data
    )
    response.raise_for_status()
    return response.json()["access_token"]
