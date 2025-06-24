import requests
from difflib import get_close_matches
from marktplaats_auth import get_marktplaats_access_token

MARKTPLAATS_API_BASE = "https://api.marktplaats.nl/v1"

def fetch_category_attributes(category_id):
    """Fetch available attributes for a given category."""
    token = get_marktplaats_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Language": "nl-NL",
    }
    url = f"{MARKTPLAATS_API_BASE}/categories/{category_id}/attributes"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("_embedded", {}).get("mp:attribute", [])

def _normalize_ai_attributes(ai_attributes):
    """Convert AI attribute output to a list of {name, value} dicts."""
    if isinstance(ai_attributes, dict):
        return [{"name": k, "value": v} for k, v in ai_attributes.items()]
    if isinstance(ai_attributes, list):
        norm = []
        for item in ai_attributes:
            if isinstance(item, dict) and "name" in item and "value" in item:
                norm.append({"name": item["name"], "value": item["value"]})
        return norm
    return []

def map_ai_attributes_to_marktplaats(ai_attributes, mp_attributes):
    """Map AI generated attributes to Marktplaats attribute IDs."""
    normalized = _normalize_ai_attributes(ai_attributes)
    name_to_attr = {}
    for attr in mp_attributes:
        label = attr.get("labels", {}).get("nl-NL") or attr.get("name")
        if label:
            name_to_attr[label] = attr
    mapped = []
    for ai_attr in normalized:
        matches = get_close_matches(ai_attr["name"], name_to_attr.keys(), n=1, cutoff=0.6)
        if matches:
            match = name_to_attr[matches[0]]
            mapped.append({"id": match["id"], "value": ai_attr["value"]})
    return mapped
