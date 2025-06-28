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


def list_user_advertisements(user_id, offset=None, limit=None):
    """
    List advertisements for a specific user.
    
    Args:
        user_id (str): User ID for token retrieval
        offset (int): Optional offset for pagination
        limit (int): Optional limit for pagination (max 100)
        
    Returns:
        dict: List of user's advertisements
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If user token is invalid
    """
    if not user_id:
        raise ValueError("User ID is required")
    
    # Get user-specific token
    token = get_user_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    # Build query parameters
    params = {}
    if offset is not None:
        params['offset'] = offset
    if limit is not None:
        params['limit'] = min(limit, 100)  # API max is 100
    
    print(f"Listing advertisements for user {user_id} with params: {params}")
    
    # First get the actual Marktplaats user ID
    me_response = requests.get(
        f"{MARKTPLAATS_API_BASE}/me",
        headers=headers,
        allow_redirects=False  # Don't follow redirects so we can get the Location header
    )
    
    print(f"ME response status: {me_response.status_code}")
    print(f"ME response headers: {dict(me_response.headers)}")
    
    # Extract Marktplaats user ID from the redirect location header
    if me_response.status_code == 302 and 'location' in me_response.headers:
        location = me_response.headers['location']
        # Extract user ID from /v1/users/{userId}
        marktplaats_user_id = location.split('/')[-1]
        print(f"Found Marktplaats user ID: {marktplaats_user_id}")
    else:
        print(f"Unexpected ME response: {me_response.status_code}, {me_response.text}")
        raise ValueError(f"Could not determine Marktplaats user ID. Status: {me_response.status_code}")
    
    response = requests.get(
        f"{MARKTPLAATS_API_BASE}/users/{marktplaats_user_id}/advertisements",
        headers=headers,
        params=params if params else None
    )
    
    print(f"List advertisements response status: {response.status_code}")
    print(f"List advertisements response body: {response.text}")
    
    response.raise_for_status()
    return response.json()


def get_user_advertisement(advertisement_id, user_id):
    """
    Get advertisement details for a specific user's advertisement.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        user_id (str): User ID for token retrieval
        
    Returns:
        dict: Advertisement details
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If user token is invalid
    """
    if not advertisement_id:
        raise ValueError("Advertisement ID is required")
    if not user_id:
        raise ValueError("User ID is required")
    
    # Get user-specific token
    token = get_user_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    print(f"Getting advertisement {advertisement_id} for user {user_id}")
    
    # Use the standard advertisement endpoint (not user-specific)
    response = requests.get(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers=headers
    )
    
    print(f"Get advertisement response status: {response.status_code}")
    print(f"Get advertisement response body: {response.text}")
    
    response.raise_for_status()
    return response.json()


def update_user_advertisement(advertisement_id, user_id, title=None, description=None, price_model=None, attributes=None):
    """
    Update an existing advertisement for a specific user using PATCH with JSON Patch operations.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        user_id (str): User ID for token retrieval
        title (str): Optional new title
        description (str): Optional new description
        price_model (dict): Optional new price model with askingPrice
        attributes (list): Optional new attributes
        
    Returns:
        dict: Update response
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If parameters are invalid
    """
    if not advertisement_id:
        raise ValueError("Advertisement ID is required")
    if not user_id:
        raise ValueError("User ID is required")
    
    # Get user-specific token
    token = get_user_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json-patch+json",
        "Accept": "application/json"
    }
    
    # Build JSON Patch operations
    patch_operations = []
    
    if title is not None:
        patch_operations.append({
            "op": "replace",
            "path": "/title",  
            "value": title
        })
    
    if description is not None:
        patch_operations.append({
            "op": "replace",
            "path": "/description",
            "value": description
        })
    
    if price_model is not None and 'askingPrice' in price_model:
        new_asking_price = price_model['askingPrice']
        print(f"Updating asking price to {new_asking_price}")
        
        # Add operation to update asking price
        patch_operations.append({
            "op": "replace",
            "path": "/priceModel/askingPrice",
            "value": new_asking_price
        })
        
        # Get current advertisement to check if we need to adjust minimalBid
        print(f"Getting current advertisement to check minimalBid...")
        current_ad_response = requests.get(
            f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )
        
        if current_ad_response.status_code == 200:
            current_ad = current_ad_response.json()
            current_price_model = current_ad.get('priceModel', {})
            current_minimal_bid = current_price_model.get('minimalBid')
            
            print(f"Current price model: {current_price_model}")
            
            # Adjust minimalBid if it exists and is greater than new askingPrice
            if current_minimal_bid is not None and current_minimal_bid > new_asking_price:
                new_minimal_bid = new_asking_price - 1
                print(f"Adjusting minimalBid from {current_minimal_bid} to {new_minimal_bid}")
                
                patch_operations.append({
                    "op": "replace",
                    "path": "/priceModel/minimalBid",
                    "value": new_minimal_bid
                })
    
    if attributes is not None:
        patch_operations.append({
            "op": "replace",
            "path": "/attributes",
            "value": attributes
        })
    
    if not patch_operations:
        raise ValueError("At least one field must be provided for update")
    
    # Validate title length before sending to API
    for operation in patch_operations:
        if operation.get("path") == "/title" and len(operation.get("value", "")) > 80:
            raise ValueError(f"Title is too long ({len(operation['value'])} characters). Maximum is 80 characters.")
    
    print(f"Updating advertisement {advertisement_id} for user {user_id}")
    print(f"JSON Patch operations: {patch_operations}")
    
    # Debug: Print the actual JSON being sent
    import json as json_module
    json_payload = json_module.dumps(patch_operations, ensure_ascii=False)
    print(f"JSON Patch payload being sent: {json_payload}")
    print(f"JSON Patch payload length: {len(json_payload)}")
    
    response = requests.patch(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers=headers,
        json=patch_operations
    )
    
    print(f"Update advertisement response status: {response.status_code}")
    print(f"Update advertisement response body: {response.text}")
    
    # Handle Marktplaats API validation errors more gracefully
    if response.status_code == 400:
        try:
            error_data = response.json()
            if error_data.get("code") == "validation-failure":
                details = error_data.get("details", [])
                error_messages = []
                for detail in details:
                    field = detail.get("field", "unknown")
                    message = detail.get("message", "validation error")
                    error_messages.append(f"{field}: {message}")
                raise ValueError("Marktplaats validation error: " + "; ".join(error_messages))
        except (ValueError, KeyError):
            pass  # Fall through to the original error handling
    
    response.raise_for_status()
    return response.json()


def get_user_advertisement_images(advertisement_id, user_id):
    """
    Get images for a user's advertisement.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        user_id (str): User ID for token retrieval
        
    Returns:
        dict: Advertisement images response
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If parameters are invalid
    """
    if not advertisement_id:
        raise ValueError("Advertisement ID is required")
    if not user_id:
        raise ValueError("User ID is required")
    
    # Get user-specific token
    token = get_user_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    print(f"Getting images for advertisement {advertisement_id} for user {user_id}")
    
    response = requests.get(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}/images",
        headers=headers
    )
    
    print(f"Get advertisement images response status: {response.status_code}")
    print(f"Get advertisement images response body: {response.text}")
    
    response.raise_for_status()
    return response.json()


def toggle_advertisement_reserved_status(advertisement_id, user_id, reserved_status, asking_price=None):
    """
    Toggle the reserved status of an advertisement using JSON Patch.
    
    According to Marktplaats API docs: "if set to true, this will override 
    the advertisement Price Model and set it to reserved."
    
    To unreserve, we need to provide a new asking price (like the Marktplaats website does).
    
    Args:
        advertisement_id (str/int): Advertisement ID
        user_id (str): User ID for token retrieval
        reserved_status (bool): New reserved status (True for reserved, False for available)
        asking_price (int): Required when unreserving (reserved_status=False). Price in cents.
        
    Returns:
        dict: Update response
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If parameters are invalid
    """
    if not advertisement_id:
        raise ValueError("Advertisement ID is required")
    if not user_id:
        raise ValueError("User ID is required")
    if not isinstance(reserved_status, bool):
        raise ValueError("Reserved status must be a boolean")
    
    # When unreserving, asking price is required
    if not reserved_status and not asking_price:
        raise ValueError("Asking price is required when unreserving an advertisement")
    
    if asking_price and (not isinstance(asking_price, int) or asking_price <= 0):
        raise ValueError("Asking price must be a positive integer (in cents)")
    
    # Get user-specific token
    token = get_user_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json-patch+json",
        "Accept": "application/json"
    }
    
    print(f"Updating reserved status for advertisement {advertisement_id} to {reserved_status}")
    
    # Get current advertisement data first to understand current state
    current_response = requests.get(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
    )
    
    current_data = None
    if current_response.status_code == 200:
        current_data = current_response.json()
        current_reserved = current_data.get('reserved', False)
        current_price_model = current_data.get('priceModel', {})
        
        print(f"Current advertisement state:")
        print(f"  - reserved: {current_reserved}")
        print(f"  - priceModel: {current_price_model}")
        
        # Debug: Let's see what other price-related fields are available
        print(f"  - All advertisement fields: {list(current_data.keys())}")
        
        # Look for any price-related fields outside the price model
        for key, value in current_data.items():
            if 'price' in key.lower() or 'bid' in key.lower() or 'amount' in key.lower():
                print(f"  - Found price-related field {key}: {value}")
        
        # If we're trying to unreserve but it's already not reserved, no need to update
        if not reserved_status and not current_reserved:
            print("Advertisement is already not reserved, no update needed")
            return current_data
        
        # If we're trying to reserve but it's already reserved, no need to update  
        if reserved_status and current_reserved:
            print("Advertisement is already reserved, no update needed")
            return current_data
    
    # Build JSON Patch operations based on whether we're reserving or unreserving
    if reserved_status:
        # Reserving: simply set reserved to true (this will override price model)
        print("Reserving advertisement by setting reserved=true...")
        patch_operations = [{
            "op": "replace",
            "path": "/reserved",
            "value": True
        }]
    else:
        # Unreserving: need to restore the original price model and remove reserved field
        print("Unreserving advertisement by restoring price model...")
        
        # To unreserve, we need to:
        # 1. Remove the reserved field  
        # 2. Restore a complete price model with the user-provided asking price
        
        print(f"Unreserving advertisement with new asking price: {asking_price} cents")
        
        # Create a complete fixed price model with the provided asking price
        restore_price_model = {
            "modelType": "fixed",
            "askingPrice": asking_price
        }
        
        print(f"Restoring price model: {restore_price_model}")
        
        # Use two operations: set proper price model and remove reserved field
        patch_operations = [
            {
                "op": "replace",
                "path": "/priceModel/modelType",
                "value": restore_price_model["modelType"]
            },
            {
                "op": "add",
                "path": "/priceModel/askingPrice",
                "value": restore_price_model["askingPrice"]
            }
        ]
    
    print(f"JSON Patch operations: {patch_operations}")
    
    response = requests.patch(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers=headers,
        json=patch_operations
    )
    
    print(f"Toggle reserved status response status: {response.status_code}")
    print(f"Toggle reserved status response body: {response.text}")
    
    # Handle Marktplaats API validation errors more gracefully
    if response.status_code == 400:
        try:
            error_data = response.json()
            if error_data.get("code") == "validation-failure":
                details = error_data.get("details", [])
                error_messages = []
                for detail in details:
                    field = detail.get("field", "unknown")
                    message = detail.get("message", "validation error")
                    error_messages.append(f"{field}: {message}")
                print(f"Marktplaats validation error: {'; '.join(error_messages)}")
                
                # If unreserving failed, try simpler approaches
                if not reserved_status:
                    print("Complex unreserve operation failed, trying simpler approaches...")
                    
                    # Try 1: Just remove the reserved field
                    print("Trying to remove reserved field only...")
                    fallback_operations = [{
                        "op": "remove",
                        "path": "/reserved"
                    }]
                    
                    fallback_response = requests.patch(
                        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
                        headers=headers,
                        json=fallback_operations
                    )
                    
                    print(f"Fallback 1 response status: {fallback_response.status_code}")
                    
                    if fallback_response.ok:
                        response = fallback_response
                    else:
                        # Try 2: Just set reserved to false
                        print("Trying to set reserved to false...")
                        fallback_operations_2 = [{
                            "op": "replace",
                            "path": "/reserved", 
                            "value": False
                        }]
                        
                        fallback_response_2 = requests.patch(
                            f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
                            headers=headers,
                            json=fallback_operations_2
                        )
                        
                        print(f"Fallback 2 response status: {fallback_response_2.status_code}")
                        
                        if fallback_response_2.ok:
                            response = fallback_response_2
                        else:
                            raise ValueError("Cannot unreserve advertisement. Marktplaats API error: " + "; ".join(error_messages))
                else:
                    raise ValueError("Marktplaats validation error: " + "; ".join(error_messages))
        except (ValueError, KeyError):
            pass  # Fall through to the original error handling
    
    response.raise_for_status()
    
    # Get the updated advertisement to verify the change actually took effect
    print(f"Verifying reserved status change...")
    verify_response = requests.get(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
    )
    
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        actual_reserved = verify_data.get('reserved', False)
        print(f"Verification: Expected reserved={reserved_status}, Actual reserved={actual_reserved}")
        
        if actual_reserved != reserved_status:
            print(f"WARNING: Reserved status did not change as expected!")
            if not reserved_status:
                print("Failed to unreserve advertisement. This might be due to:")
                print("1. Incomplete price model restoration")
                print("2. API timing issues")
                print("3. Missing required price model fields")
                verify_data['warning'] = f"Could not unreserve advertisement. Expected reserved={reserved_status}, but got reserved={actual_reserved}. The price model restoration may have failed."
            else:
                verify_data['warning'] = f"Could not reserve advertisement. API returned reserved={actual_reserved} instead of {reserved_status}."
            return verify_data
        else:
            print(f"✅ Reserved status successfully updated to {actual_reserved}")
    
    return response.json()


def delete_user_advertisement(advertisement_id, user_id):
    """
    Delete an advertisement for a specific user.
    
    Args:
        advertisement_id (str/int): Advertisement ID
        user_id (str): User ID for token retrieval
        
    Returns:
        dict: Delete response
        
    Raises:
        requests.HTTPError: If API call fails
        ValueError: If parameters are invalid
    """
    if not advertisement_id:
        raise ValueError("Advertisement ID is required")
    if not user_id:
        raise ValueError("User ID is required")
    
    # Get user-specific token
    token = get_user_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    print(f"Deleting advertisement {advertisement_id} for user {user_id}")
    
    response = requests.delete(
        f"{MARKTPLAATS_API_BASE}/advertisements/{advertisement_id}",
        headers=headers
    )
    
    print(f"Delete advertisement response status: {response.status_code}")
    print(f"Delete advertisement response body: {response.text}")
    
    response.raise_for_status()
    return response.json() if response.text else {"success": True}