import os
import requests
from .marktplaats_auth import get_marktplaats_access_token, get_user_token

if os.environ.get("IS_LOCAL"):
    from dotenv import load_dotenv
    load_dotenv()

MARKTPLAATS_API_BASE = "https://api.marktplaats.nl/v1"


def create_advertisement(title, description, category_id, postcode, price_model, attributes=None, user_id=None):
    """
    Create a new advertisement on Marktplaats.
    
    Args:
        title (str): Advertisement title
        description (str): Advertisement description  
        category_id (int): Marktplaats category ID
        postcode (str): Location postcode
        price_model (dict): Price model with modelType and askingPrice
        attributes (list): List of category-specific attributes
        user_id (str): User ID for token retrieval (if None, uses client token)
        
    Returns:
        dict: Advertisement creation response with ID and links
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If required fields are missing
    """
    # Validate required fields
    if not all([title, description, category_id, postcode, price_model]):
        raise ValueError("Missing required fields for advertisement creation")
    
    if not isinstance(price_model, dict) or 'modelType' not in price_model:
        raise ValueError("Invalid price_model format")
    
    # Get access token (user token if user_id provided, otherwise client token)
    if user_id:
        try:
            token = get_user_token(user_id)
        except ValueError as e:
            print(f"Warning: Failed to get user token for {user_id}: {str(e)}. Falling back to client credentials.")
            token = get_marktplaats_access_token()
    else:
        token = get_marktplaats_access_token()
    
    # Build request payload
    payload = {
        "title": title,
        "description": description,
        "categoryId": category_id,
        "location": {
            "postcode": postcode
        },
        "priceModel": price_model
    }
    
    # Add attributes if provided
    if attributes:
        payload["attributes"] = attributes
    
    # Make API request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"Creating advertisement with payload: {payload}")
    print(f"Using headers: {headers}")
    
    response = requests.post(
        f"{MARKTPLAATS_API_BASE}/advertisements",
        headers=headers,
        json=payload
    )
    
    print(f"Advertisement creation response status: {response.status_code}")
    print(f"Advertisement creation response body: {response.text}")
    
    response.raise_for_status()
    return response.json()


def upload_advertisement_images(advertisement_id, image_urls, replace_all=False, user_id=None):
    """
    Upload images to an existing advertisement.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        image_urls (list): List of public image URLs
        replace_all (bool): Whether to replace existing images
        user_id (str): User ID for token retrieval (if None, uses client token)
        
    Returns:
        dict: Image upload response
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If parameters are invalid
    """
    if not advertisement_id:
        raise ValueError("Advertisement ID is required")
    
    if not image_urls or not isinstance(image_urls, list):
        raise ValueError("image_urls must be a non-empty list")
    
    # Get access token (user token if user_id provided, otherwise client token)
    if user_id:
        try:
            token = get_user_token(user_id)
        except ValueError as e:
            print(f"Warning: Failed to get user token for {user_id}: {str(e)}. Falling back to client credentials.")
            token = get_marktplaats_access_token()
    else:
        token = get_marktplaats_access_token()
    
    # Build request payload
    payload = {
        "urls": image_urls
    }
    
    if replace_all:
        payload["replaceAll"] = True
    
    # Make API request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"Uploading images to advertisement {advertisement_id}")
    print(f"Image upload payload: {payload}")
    print(f"Image upload headers: {headers}")
    
    response = requests.post(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}/images",
        headers=headers,
        json=payload
    )
    
    print(f"Image upload response status: {response.status_code}")
    print(f"Image upload response body: {response.text}")
    
    response.raise_for_status()
    return response.json()


def get_advertisement(advertisement_id):
    """
    Retrieve advertisement details.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        
    Returns:
        dict: Advertisement details
        
    Raises:
        requests.HTTPError: If API call fails
    """
    token = get_marktplaats_access_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers=headers
    )
    
    response.raise_for_status()
    return response.json()


def get_advertisement_images(advertisement_id):
    """
    Get images for an advertisement.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        
    Returns:
        dict: Advertisement images response
        
    Raises:
        requests.HTTPError: If API call fails
    """
    token = get_marktplaats_access_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}/images",
        headers=headers
    )
    
    response.raise_for_status()
    return response.json()


def validate_advertisement_data(listing_data, postcode, price_model):
    """
    Validate advertisement data before submission.
    
    Args:
        listing_data (dict): Generated listing data
        postcode (str): Location postcode
        price_model (dict): Price model
        
    Returns:
        list: List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    if not listing_data.get('title'):
        errors.append("Title is required")
    elif len(listing_data['title']) > 80:
        errors.append("Title must be 80 characters or less")
        
    if not listing_data.get('description'):
        errors.append("Description is required")
        
    if not listing_data.get('categoryId'):
        errors.append("Category ID is required")
        
    if not postcode:
        errors.append("Postcode is required")
    elif len(postcode.replace(' ', '')) != 6:
        errors.append("Postcode must be 6 characters (including space)")
        
    if not price_model:
        errors.append("Price model is required")
    elif not isinstance(price_model, dict):
        errors.append("Price model must be an object")
    elif 'modelType' not in price_model:
        errors.append("Price model must include modelType")
    elif price_model['modelType'] not in ['fixed', 'bidding', 'notApplicable']:
        errors.append("Invalid price model type")
        
    return errors


def get_me():
    """
    Get current user information from Marktplaats API.
    
    Returns:
        dict: User information including ID, type, and permissions
        
    Raises:
        requests.HTTPError: If API call fails
    """
    token = get_marktplaats_access_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    response = requests.get(
        f"{MARKTPLAATS_API_BASE}/me",
        headers=headers
    )
    
    response.raise_for_status()
    return response.json()