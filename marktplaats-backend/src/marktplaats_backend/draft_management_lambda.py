import json
import os
from typing import Dict, Any

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .draft_storage import (
    DraftListing, create_draft, get_draft, list_user_drafts, 
    update_draft, delete_draft, get_draft_count_by_user,
    validate_draft_for_publishing
)


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
        
        # Handle OPTIONS preflight request
        if http_method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": get_cors_headers(),
                "body": ""
            }
        
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
    
    # Convert DraftListing objects to dictionaries
    drafts_data = [draft.to_dict() for draft in result['drafts']]
    
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
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps(draft.to_dict())
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
        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
        "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS"
    }