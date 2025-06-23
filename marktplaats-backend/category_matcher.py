import requests
from difflib import get_close_matches

MARKTPLAATS_API_BASE = "https://api.marktplaats.nl/v1"
MARKTPLAATS_AUTH_HEADER = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",  # Replace with actual token securely
    "Accept-Language": "nl-NL"  # 👈 Ensures Dutch category names
}


def fetch_marktplaats_categories():
    response = requests.get(f"{MARKTPLAATS_API_BASE}/categories", headers=MARKTPLAATS_AUTH_HEADER)
    response.raise_for_status()
    return response.json()


def flatten_categories(categories, parent_path=""):
    flat = []
    for cat in categories:
        name = f"{parent_path} > {cat['name']}" if parent_path else cat["name"]
        flat.append({"name": name.strip(), "id": cat["id"]})
        if "children" in cat and isinstance(cat["children"], list):
            flat.extend(flatten_categories(cat["children"], name))
    return flat


def match_category(dutch_category_path, flat_categories):
    names = {cat["name"]: cat["id"] for cat in flat_categories}
    match = get_close_matches(dutch_category_path, names.keys(), n=1, cutoff=0.6)
    if match:
        return {"match": match[0], "categoryId": names[match[0]]}
    return None


# Example usage
if __name__ == "__main__":
    cats = fetch_marktplaats_categories()
    flat = flatten_categories(cats)
    result = match_category("Speelgoed & Spel > Buitenspeelgoed > Fietsen & Voertuigen", flat)
    print(result)
