import os

if os.environ.get("IS_LOCAL"):
    from dotenv import load_dotenv
    load_dotenv()

from difflib import get_close_matches

import requests
from marktplaats_auth import get_marktplaats_access_token

MARKTPLAATS_API_BASE = "https://api.marktplaats.nl/v1"


def fetch_marktplaats_categories():
    token = get_marktplaats_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Language": "nl-NL",
    }
    response = requests.get(f"{MARKTPLAATS_API_BASE}/categories", headers=headers)
    response.raise_for_status()
    return response.json()["_embedded"]["mp:category"]


def flatten_categories(categories, parent_path=""):
    flat = []
    for cat in categories:
        name = cat["labels"].get("nl-NL", cat["name"])
        full_path = f"{parent_path} > {name}" if parent_path else name
        flat.append({"name": full_path.strip(), "id": cat["categoryId"]})
        children = cat.get("_embedded", {}).get("mp:category", [])
        flat.extend(flatten_categories(children, full_path))
    return flat

def match_category(suggested_path, flat_categories):
    name_to_id = {cat["name"]: cat["id"] for cat in flat_categories}
    matches = get_close_matches(suggested_path, name_to_id.keys(), n=1, cutoff=0.6)
    if matches:
        match_name = matches[0]
        return {"match": match_name, "categoryId": name_to_id[match_name]}
    return None

def simplify_path(path):
    parts = [p.strip() for p in path.split('>')]
    if len(parts) >= 2:
        return f"{parts[0]} > {parts[-1]}"
    return path.strip()

def match_category_name(suggested_path, flat_categories):
    simplified_path = simplify_path(suggested_path)
    name_to_id = {cat["name"]: cat["id"] for cat in flat_categories}
    matches = get_close_matches(simplified_path, name_to_id.keys(), n=1, cutoff=0.6)
    if matches:
        match_name = matches[0]
        return {"match": match_name, "categoryId": name_to_id[match_name]}
    return None

# Optional test harness
if __name__ == "__main__":
    cats = fetch_marktplaats_categories()
    flat = flatten_categories(cats)
    # print(flat)
    #"Speelgoed & Spel > Buitenspeelgoed > Fietsen & Voertuigen"
    result = match_category_name(
        "Speelgoed & Spel > Buitenspeelgoed > Fietsen & Voertuigen", flat
    )
    print(result)
