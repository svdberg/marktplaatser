import os
import urllib.parse
import boto3
import json

if os.environ.get("IS_LOCAL"):
    from dotenv import load_dotenv
    load_dotenv()

import requests

# Force AWS region to eu-west-1
os.environ['AWS_REGION'] = 'eu-west-1'

MARKTPLAATS_AUTH_BASE = "https://auth.marktplaats.nl/accounts/oauth"


def get_marktplaats_client_token():
    """
    Get client credentials token (for public API access like categories).
    """
    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    print(f"Client credentials request data: {data}")
    
    response = requests.post(
        f"{MARKTPLAATS_AUTH_BASE}/token", headers=headers, data=data
    )
    
    print(f"Client credentials response status: {response.status_code}")
    print(f"Client credentials response body: {response.text}")
    
    response.raise_for_status()
    return response.json()["access_token"]


def get_authorization_url(redirect_uri, state=None):
    """
    Generate OAuth authorization URL for user consent.
    
    Args:
        redirect_uri (str): Callback URL after authorization
        state (str): Optional state parameter for CSRF protection
        
    Returns:
        str: Authorization URL to redirect user to
    """
    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    
    if state:
        params["state"] = state
    
    query_string = urllib.parse.urlencode(params)
    return f"{MARKTPLAATS_AUTH_BASE}/authorize?{query_string}"


def exchange_code_for_token(authorization_code, redirect_uri):
    """
    Exchange authorization code for access token.
    
    Args:
        authorization_code (str): Code received from authorization callback
        redirect_uri (str): Same redirect URI used in authorization
        
    Returns:
        dict: Token response with access_token, refresh_token, etc.
    """
    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }

    print(f"Token exchange request data: {data}")
    
    response = requests.post(
        f"{MARKTPLAATS_AUTH_BASE}/token", headers=headers, data=data
    )
    
    print(f"Token exchange response status: {response.status_code}")
    print(f"Token exchange response body: {response.text}")
    
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token):
    """
    Refresh an expired access token.
    
    Args:
        refresh_token (str): Refresh token
        
    Returns:
        dict: New token response
    """
    client_id = os.environ["MARKTPLAATS_CLIENT_ID"]
    client_secret = os.environ["MARKTPLAATS_CLIENT_SECRET"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(
        f"{MARKTPLAATS_AUTH_BASE}/token", headers=headers, data=data
    )
    response.raise_for_status()
    return response.json()


def store_user_tokens(user_id, token_data):
    """
    Store user tokens in DynamoDB.
    
    Args:
        user_id (str): Unique user identifier
        token_data (dict): Token response from OAuth
    """
    session = boto3.Session(region_name="eu-west-1")
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('marktplaats-user-tokens')
    
    table.put_item(
        Item={
            'user_id': user_id,
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data.get('expires_in'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'scope': token_data.get('scope'),
            'created_at': int(__import__('time').time())
        }
    )


def get_user_token(user_id):
    """
    Retrieve user token from DynamoDB.
    
    Args:
        user_id (str): User identifier
        
    Returns:
        str: Valid access token (refreshed if needed)
    """
    session = boto3.Session(region_name="eu-west-1")
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('marktplaats-user-tokens')
    
    try:
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            raise ValueError(f"No tokens found for user {user_id}")
        
        item = response['Item']
        
        # Check if token is expired (with 5 min buffer)
        created_at = item['created_at']
        expires_in = item.get('expires_in', 86400)  # Default 24h
        current_time = int(__import__('time').time())
        
        if current_time >= (created_at + expires_in - 300):  # 5 min buffer
            # Token expired, refresh it
            if item.get('refresh_token'):
                new_token_data = refresh_access_token(item['refresh_token'])
                store_user_tokens(user_id, new_token_data)
                return new_token_data['access_token']
            else:
                raise ValueError(f"Token expired and no refresh token for user {user_id}")
        
        return item['access_token']
        
    except Exception as e:
        raise ValueError(f"Failed to get user token: {str(e)}")


# Backward compatibility
def get_marktplaats_access_token():
    """Legacy function - returns client token."""
    return get_marktplaats_client_token()
