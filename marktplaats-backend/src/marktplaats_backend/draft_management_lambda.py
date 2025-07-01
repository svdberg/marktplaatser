import json
import os
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .draft_storage import (
    DraftListing, create_draft, get_draft, list_user_drafts, 
    update_draft, delete_draft, get_draft_count_by_user,
    validate_draft_for_publishing
)
from .marktplaats_ads_api import (
    create_advertisement,
    upload_advertisement_images,
    validate_advertisement_data
)
from .marktplaats_auth import get_marktplaats_user_id, get_user_token

# Initialize S3 client
s3 = boto3.client('s3', region_name='eu-west-1')


def resolve_marktplaats_user_id(internal_user_id: str) -> str:
    """
    Convert internal user ID to Marktplaats user ID for consistent draft storage.
    
    Args:
        internal_user_id: Internal user ID from frontend
        
    Returns:
        str: Marktplaats user ID
        
    Raises:
        ValueError: If user token is invalid or Marktplaats ID cannot be determined
    """
    try:
        # Get user's access token using internal ID
        access_token = get_user_token(internal_user_id)
        
        # Extract Marktplaats user ID from token
        marktplaats_user_id = get_marktplaats_user_id(access_token)
        
        print(f"Resolved internal user {internal_user_id} to Marktplaats user {marktplaats_user_id}")
        return marktplaats_user_id
        
    except Exception as e:
        print(f"Failed to resolve Marktplaats user ID for {internal_user_id}: {str(e)}")
        raise ValueError(f"Could not resolve user identity: {str(e)}")


def refresh_presigned_urls(draft_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert old presigned URLs to public URLs if needed.
    
    Args:
        draft_data: Draft data dictionary
        
    Returns:
        Draft data with public URLs
    """
    if not draft_data.get('images'):
        return draft_data
    
    s3_bucket = os.environ.get('S3_BUCKET', 'marktplaatser-images')
    refreshed_images = []
    
    for image_url in draft_data['images']:
        try:
            # Convert presigned URLs to public URLs
            if 'amazonaws.com' in image_url and 'drafts/' in image_url:
                # Extract the key from the URL
                key_start = image_url.find('drafts/')
                key_end = image_url.find('?') if '?' in image_url else len(image_url)
                s3_key = image_url[key_start:key_end] if key_end > key_start else None
                
                if s3_key:
                    # Generate public URL
                    public_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
                    refreshed_images.append(public_url)
                else:
                    # Keep original if we can't parse it
                    refreshed_images.append(image_url)
            else:
                # Keep non-S3 URLs as-is
                refreshed_images.append(image_url)
                
        except Exception as e:
            print(f"Error converting URL for {image_url}: {str(e)}")
            # Keep original URL if conversion fails
            refreshed_images.append(image_url)
    
    # Update the draft data with public URLs
    draft_data['images'] = refreshed_images
    return draft_data


def lambda_handler(event, context):
    """
    Lambda function to manage draft listings (CRUD operations).
    
    Expected event formats:
    - GET /drafts:                           List user's drafts
    - POST /drafts:                          Create new draft
    - GET /drafts/{id}:                      Get specific draft
    - PATCH /drafts/{id}:                    Update draft
    - DELETE /drafts/{id}:                   Delete draft
    - POST /drafts/{id}/validate:            Validate draft for publishing
    - POST /drafts/{id}/publish:             Publish draft to Marktplaats
    
    All operations require user_id query parameter for authentication.
    """
    try:
        # Extract HTTP method and path parameters
        http_method = event.get('httpMethod', '').upper()
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        path = event.get('path', '')
        
        # Handle OPTIONS preflight request first (before validation)
        if http_method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": get_cors_headers(),
                "body": ""
            }
        
        draft_id = path_params.get('id')
        internal_user_id = query_params.get('user_id')
        
        # Check if this is a validate or publish endpoint by looking at the path
        is_validate_endpoint = '/validate' in path
        is_publish_endpoint = '/publish' in path
        
        # Validate required parameters
        if not internal_user_id:
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "user_id query parameter is required"})
            }
        
        # Resolve to Marktplaats user ID for consistent draft storage
        try:
            marktplaats_user_id = resolve_marktplaats_user_id(internal_user_id)
        except ValueError as e:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": str(e)})
            }
        
        print(f"Managing drafts for Marktplaats user {marktplaats_user_id} (internal: {internal_user_id}) via {http_method} {event.get('path', '')}")
        
        try:
            if http_method == 'GET' and not draft_id:
                # List user's drafts: GET /drafts
                return handle_list_drafts(marktplaats_user_id, internal_user_id, query_params)
                
            elif http_method == 'POST' and not draft_id:
                # Create new draft: POST /drafts
                return handle_create_draft(marktplaats_user_id, event.get('body'))
                
            elif http_method == 'GET' and draft_id:
                # Get specific draft: GET /drafts/{id}
                return handle_get_draft(draft_id, marktplaats_user_id, internal_user_id)
                
            elif http_method == 'PATCH' and draft_id:
                # Update draft: PATCH /drafts/{id}
                return handle_update_draft(draft_id, marktplaats_user_id, internal_user_id, event.get('body'))
                
            elif http_method == 'DELETE' and draft_id:
                # Delete draft: DELETE /drafts/{id}
                return handle_delete_draft(draft_id, marktplaats_user_id, internal_user_id)
                
            elif http_method == 'POST' and draft_id and is_validate_endpoint:
                # Validate draft: POST /drafts/{id}/validate
                return handle_validate_draft(draft_id, marktplaats_user_id, internal_user_id)
                
            elif http_method == 'POST' and draft_id and is_publish_endpoint:
                # Publish draft: POST /drafts/{id}/publish
                return handle_publish_draft(draft_id, marktplaats_user_id, internal_user_id, event.get('body'))
                
            else:
                return {
                    "statusCode": 405,
                    "headers": get_cors_headers(),
                    "body": json.dumps({"error": f"Method {http_method} not allowed for this endpoint"})
                }
                
        except ValueError as e:
            # Handle validation errors and user input errors
            print(f"Validation error for Marktplaats user {marktplaats_user_id}: {str(e)}")
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": str(e)})
            }
            
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Internal server error"})
        }


def handle_list_drafts(marktplaats_user_id: str, internal_user_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /drafts - List user's draft listings with hybrid search for migration."""
    limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
    last_evaluated_key = query_params.get('last_evaluated_key')
    
    # Try with Marktplaats user ID first (new format)
    result = list_user_drafts(marktplaats_user_id, limit, last_evaluated_key)
    
    # If no drafts found with Marktplaats user ID, try with internal user ID (legacy format)
    if not result['drafts']:
        print(f"No drafts found for Marktplaats user {marktplaats_user_id}, trying legacy internal user {internal_user_id}")
        legacy_result = list_user_drafts(internal_user_id, limit, last_evaluated_key)
        if legacy_result['drafts']:
            print(f"Found {len(legacy_result['drafts'])} legacy drafts for internal user {internal_user_id}")
            result = legacy_result
    
    # Convert DraftListing objects to dictionaries and refresh presigned URLs
    drafts_data = []
    for draft in result['drafts']:
        draft_dict = draft.to_dict()
        # Refresh presigned URLs for images
        draft_dict = refresh_presigned_urls(draft_dict)
        drafts_data.append(draft_dict)
    
    response_data = {
        'drafts': drafts_data,
        'count': len(drafts_data)
    }
    
    if 'last_evaluated_key' in result:
        response_data['last_evaluated_key'] = result['last_evaluated_key']
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps(response_data)
    }


def handle_create_draft(user_id: str, body: str) -> Dict[str, Any]:
    """Handle POST /drafts - Create new draft listing."""
    if not body:
        raise ValueError("Request body is required")
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in request body")
    
    # Create DraftListing from request data
    draft = DraftListing(
        user_id=user_id,
        title=data.get('title'),
        description=data.get('description'),
        category_id=data.get('categoryId'),
        category_name=data.get('categoryName'),
        attributes=data.get('attributes', []),
        price_model=data.get('priceModel', {}),
        postcode=data.get('postcode'),
        images=data.get('images', []),
        ai_generated=data.get('aiGenerated', False),
        status=data.get('status', 'draft')
    )
    
    created_draft = create_draft(draft)
    
    return {
        "statusCode": 201,
        "headers": get_cors_headers(),
        "body": json.dumps(created_draft.to_dict())
    }


def handle_get_draft(draft_id: str, marktplaats_user_id: str, internal_user_id: str) -> Dict[str, Any]:
    """Handle GET /drafts/{id} - Get specific draft listing with hybrid search."""
    # Try with Marktplaats user ID first
    draft = get_draft(draft_id, marktplaats_user_id)
    
    # If not found, try with internal user ID (legacy)
    if not draft:
        draft = get_draft(draft_id, internal_user_id)
    
    if not draft:
        return {
            "statusCode": 404,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Draft not found"})
        }
    
    # Convert to dict and refresh presigned URLs
    draft_dict = draft.to_dict()
    draft_dict = refresh_presigned_urls(draft_dict)
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps(draft_dict)
    }


def handle_update_draft(draft_id: str, marktplaats_user_id: str, internal_user_id: str, body: str) -> Dict[str, Any]:
    """Handle PATCH /drafts/{id} - Update draft listing with hybrid search."""
    if not body:
        raise ValueError("Request body is required for updates")
    
    try:
        updates = json.loads(body)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in request body")
    
    if not updates:
        raise ValueError("At least one field must be provided for update")
    
    # Validate title length if provided
    if 'title' in updates and len(updates['title']) > 80:
        raise ValueError("Title must be 80 characters or less")
    
    # Try with Marktplaats user ID first
    updated_draft = update_draft(draft_id, marktplaats_user_id, updates)
    
    # If not found, try with internal user ID (legacy)
    if not updated_draft:
        updated_draft = update_draft(draft_id, internal_user_id, updates)
    
    if not updated_draft:
        return {
            "statusCode": 404,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Draft not found"})
        }
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps(updated_draft.to_dict())
    }


def handle_delete_draft(draft_id: str, marktplaats_user_id: str, internal_user_id: str) -> Dict[str, Any]:
    """Handle DELETE /drafts/{id} - Delete draft listing with hybrid search."""
    # Try with Marktplaats user ID first
    success = delete_draft(draft_id, marktplaats_user_id)
    
    # If not found, try with internal user ID (legacy)
    if not success:
        success = delete_draft(draft_id, internal_user_id)
    
    if not success:
        return {
            "statusCode": 404,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Draft not found"})
        }
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps({"success": True, "message": "Draft deleted successfully"})
    }


def handle_validate_draft(draft_id: str, marktplaats_user_id: str, internal_user_id: str) -> Dict[str, Any]:
    """Handle POST /drafts/{id}/validate - Validate draft for publishing with hybrid search."""
    # Try with Marktplaats user ID first
    draft = get_draft(draft_id, marktplaats_user_id)
    
    # If not found, try with internal user ID (legacy)
    if not draft:
        draft = get_draft(draft_id, internal_user_id)
    
    if not draft:
        return {
            "statusCode": 404,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Draft not found"})
        }
    
    validation_errors = validate_draft_for_publishing(draft)
    
    response_data = {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors
    }
    
    if response_data["valid"]:
        response_data["message"] = "Draft is ready for publishing"
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps(response_data)
    }


def handle_publish_draft(draft_id: str, marktplaats_user_id: str, internal_user_id: str, body: str) -> Dict[str, Any]:
    """Handle POST /drafts/{id}/publish - Publish draft to Marktplaats with hybrid search."""
    # Try with Marktplaats user ID first
    draft = get_draft(draft_id, marktplaats_user_id)
    
    # If not found, try with internal user ID (legacy)
    if not draft:
        draft = get_draft(draft_id, internal_user_id)
    
    if not draft:
        return {
            "statusCode": 404,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Draft not found"})
        }
    
    # Parse optional publishing parameters from body
    publish_params = {}
    if body:
        try:
            publish_params = json.loads(body)
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON, use defaults
    
    # Validate draft for publishing
    validation_errors = validate_draft_for_publishing(draft)
    if validation_errors:
        return {
            "statusCode": 400,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "error": "Draft validation failed",
                "details": validation_errors
            })
        }
    
    try:
        # Convert draft price from euros to cents if needed
        price_model = draft.price_model.copy() if draft.price_model else {}
        if "askingPrice" in price_model:
            # If price is in euros (< 1000), convert to cents
            if price_model["askingPrice"] < 1000:
                price_model["askingPrice"] = int(price_model["askingPrice"] * 100)
        
        # Set default price model type if not specified
        if not price_model.get("modelType"):
            price_model["modelType"] = "fixed"
        
        # Create advertisement using draft data
        ad_response = create_advertisement(
            title=draft.title,
            description=draft.description,
            category_id=draft.category_id,
            postcode=draft.postcode,
            price_model=price_model,
            attributes=draft.attributes or [],
            user_id=internal_user_id
        )
        
        advertisement_id = ad_response.get("itemId") or ad_response.get("id")
        if not advertisement_id:
            raise ValueError(f"No advertisement ID returned. Response keys: {list(ad_response.keys())}")
        
        print(f"Advertisement created from draft {draft_id} with ID: {advertisement_id}")
        
        # Upload images if available
        if draft.images:
            try:
                print(f"Uploading {len(draft.images)} images to advertisement {advertisement_id}...")
                upload_response = upload_advertisement_images(advertisement_id, draft.images, user_id=internal_user_id)
                print(f"Image upload successful: {upload_response}")
            except Exception as upload_error:
                print(f"Warning: Image upload failed but advertisement was created: {upload_error}")
                # Continue - we'll return success even if image upload fails
        
        # Optionally delete or archive the draft after successful publishing
        delete_after_publish = publish_params.get("deleteDraft", True)  # Default to delete
        if delete_after_publish:
            try:
                # Try to delete with the user ID that was used to find the draft
                success = delete_draft(draft_id, marktplaats_user_id)
                if not success:
                    success = delete_draft(draft_id, internal_user_id)
                
                if success:
                    print(f"Draft {draft_id} deleted after successful publishing")
                else:
                    print(f"Warning: Could not delete draft {draft_id} after publishing")
            except Exception as delete_error:
                print(f"Warning: Failed to delete draft after publishing: {delete_error}")
                # Continue - the advertisement was created successfully
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "message": "Draft published successfully",
                "advertisementId": advertisement_id,
                "title": ad_response.get("title"),
                "status": ad_response.get("status"),
                "websiteLink": ad_response.get("_links", {}).get("mp:advertisement-website-link", {}).get("href"),
                "draftDeleted": delete_after_publish,
                "imageCount": len(draft.images) if draft.images else 0
            })
        }
        
    except Exception as e:
        print(f"Error publishing draft {draft_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "error": "Failed to publish draft",
                "details": str(e)
            })
        }


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses."""
    return {
        "Access-Control-Allow-Origin": "*",  # Allow all origins for testing
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
        "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS"
    }