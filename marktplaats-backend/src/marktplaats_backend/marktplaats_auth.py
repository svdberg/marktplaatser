"""Utility helpers for Marktplaats OAuth authentication."""

import os
from typing import Dict

import requests

if os.environ.get("IS_LOCAL"):
    from dotenv import load_dotenv

    load_dotenv()

AUTH_BASE_URL = "https://auth.marktplaats.nl/accounts/oauth"


def get_marktplaats_access_token() -> str:
    """Retrieve an application access token using the client credentials flow."""

    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(f"{AUTH_BASE_URL}/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_authorization_url(redirect_uri: str, state: str, scope: str = "default") -> str:
    """Build the authorization URL for the user login flow."""

    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    params = (
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        f"&scope={scope}&state={state}"
    )
    return f"{AUTH_BASE_URL}/authorize?{params}"


def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, str]:
    """Exchange an authorization code for access and refresh tokens."""

    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(f"{AUTH_BASE_URL}/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def refresh_user_access_token(refresh_token: str) -> Dict[str, str]:
    """Refresh a user access token using a refresh token."""

    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(f"{AUTH_BASE_URL}/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":  # pragma: no cover - manual testing helper
    print(get_marktplaats_access_token())
