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

# Initialize S3 client
s3 = boto3.client('s3', region_name='eu-west-1')


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
        user_id = query_params.get('user_id')
        
        # Check if this is a validate endpoint by looking at the path
        is_validate_endpoint = '/validate' in path
        
        # Validate required parameters
        if not user_id:
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "user_id query parameter is required"})
            }
        
        print(f"Managing drafts for user {user_id} via {http_method} {event.get('path', '')}")
        
        try:
            if http_method == 'GET' and not draft_id:
                # List user's drafts: GET /drafts
                return handle_list_drafts(user_id, query_params)
                
            elif http_method == 'POST' and not draft_id:
                # Create new draft: POST /drafts
                return handle_create_draft(user_id, event.get('body'))
                
            elif http_method == 'GET' and draft_id:
                # Get specific draft: GET /drafts/{id}
                return handle_get_draft(draft_id, user_id)
                
            elif http_method == 'PATCH' and draft_id:
                # Update draft: PATCH /drafts/{id}
                return handle_update_draft(draft_id, user_id, event.get('body'))
                
            elif http_method == 'DELETE' and draft_id:
                # Delete draft: DELETE /drafts/{id}
                return handle_delete_draft(draft_id, user_id)
                
            elif http_method == 'POST' and draft_id and is_validate_endpoint:
                # Validate draft: POST /drafts/{id}/validate
                return handle_validate_draft(draft_id, user_id)
                
            else:
                return {
                    "statusCode": 405,
                    "headers": get_cors_headers(),
                    "body": json.dumps({"error": f"Method {http_method} not allowed for this endpoint"})
                }
                
        except ValueError as e:
            # Handle validation errors and user input errors
            print(f"Validation error for user {user_id}: {str(e)}")
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


def handle_list_drafts(user_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /drafts - List user's draft listings."""
    limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
    last_evaluated_key = query_params.get('last_evaluated_key')
    
    result = list_user_drafts(user_id, limit, last_evaluated_key)
    
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


def handle_get_draft(draft_id: str, user_id: str) -> Dict[str, Any]:
    """Handle GET /drafts/{id} - Get specific draft listing."""
    draft = get_draft(draft_id, user_id)
    
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


def handle_update_draft(draft_id: str, user_id: str, body: str) -> Dict[str, Any]:
    """Handle PATCH /drafts/{id} - Update draft listing."""
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
    
    updated_draft = update_draft(draft_id, user_id, updates)
    
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


def handle_delete_draft(draft_id: str, user_id: str) -> Dict[str, Any]:
    """Handle DELETE /drafts/{id} - Delete draft listing."""
    success = delete_draft(draft_id, user_id)
    
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


def handle_validate_draft(draft_id: str, user_id: str) -> Dict[str, Any]:
    """Handle POST /drafts/{id}/validate - Validate draft for publishing."""
    draft = get_draft(draft_id, user_id)
    
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


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses."""
    return {
        "Access-Control-Allow-Origin": "*",  # Allow all origins for testing
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
        "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS"
    }