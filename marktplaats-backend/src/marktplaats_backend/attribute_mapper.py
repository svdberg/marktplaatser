import requests
from difflib import get_close_matches
from .marktplaats_auth import get_marktplaats_access_token

MARKTPLAATS_API_BASE = "https://api.marktplaats.nl/v1"

def fetch_category_attributes(category_id, flat_categories):
    """Fetch available attributes for a given category (only works for level 2 categories)."""
    # Find the category in flat_categories to get its name
    target_category = next((cat for cat in flat_categories if cat["id"] == category_id), None)
    if not target_category:
        raise ValueError(f"Category ID {category_id} not found")
    
    # Check if this is a level 2 category (exactly one '>' separator)
    category_name = target_category["name"]
    parts = category_name.split(" > ")
    
    if len(parts) != 2:
        raise ValueError(f"Attributes only available for level 2 categories. '{category_name}' is level {len(parts)}")
    
    # Get level 1 parent category ID
    level_1_name = parts[0]
    parent_category = next((cat for cat in flat_categories if cat["name"] == level_1_name and " > " not in cat["name"]), None)
    if not parent_category:
        raise ValueError(f"Parent category '{level_1_name}' not found")
    
    # Make API call with both level 1 and level 2 IDs
    token = get_marktplaats_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Language": "nl-NL",
    }
    url = f"{MARKTPLAATS_API_BASE}/categories/{parent_category['id']}/{category_id}/attributes"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("fields", [])

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
    """Map AI generated attributes to Marktplaats attribute keys and validate values."""
    normalized = _normalize_ai_attributes(ai_attributes)
    name_to_attr = {}
    for attr in mp_attributes:
        label = attr.get("labels", {}).get("nl-NL") or attr.get("label", "")
        if label:
            name_to_attr[label] = attr
    
    mapped = []
    for ai_attr in normalized:
        matches = get_close_matches(ai_attr["name"], name_to_attr.keys(), n=1, cutoff=0.6)
        if matches:
            match = name_to_attr[matches[0]]
            attr_key = match["key"]
            ai_value = ai_attr["value"]
            
            # Handle enum/select fields with predefined values
            if "options" in match:
                valid_values = [opt.get("value", "") for opt in match["options"]]
                # Try exact match first
                if ai_value in valid_values:
                    mapped_value = ai_value
                else:
                    # Try fuzzy matching for enum values
                    value_matches = get_close_matches(ai_value, valid_values, n=1, cutoff=0.4)
                    if value_matches:
                        mapped_value = value_matches[0]
                    else:
                        # Skip invalid enum values
                        print(f"Skipping invalid enum value '{ai_value}' for field '{attr_key}'. Valid values: {valid_values}")
                        continue
            else:
                # Non-enum field, use value as-is
                mapped_value = ai_value
            
            mapped.append({"key": attr_key, "value": mapped_value})
    
    return mapped
