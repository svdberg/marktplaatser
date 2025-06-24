import json
import requests

from marktplaats_auth import get_marktplaats_access_token

MARKTPLAATS_API_BASE = "https://api.marktplaats.nl/v1"


def create_marktplaats_listing(listing):
    """Send the listing data to the Marktplaats API."""
    token = get_marktplaats_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "nl-NL",
    }
    response = requests.post(
        f"{MARKTPLAATS_API_BASE}/listings",
        headers=headers,
        json=listing,
    )
    response.raise_for_status()
    return response.json()


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        result = create_marktplaats_listing(body)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
