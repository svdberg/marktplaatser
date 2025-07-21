"""
Lambda function for uploading images to existing drafts.
"""

import json
import os
import base64
import uuid
import boto3
from .marktplaats_auth import get_marktplaats_user_id, get_user_token
from .draft_storage import get_draft, update_draft

# Force AWS region to eu-west-1
os.environ['AWS_REGION'] = 'eu-west-1'

s3 = boto3.client("s3", region_name="eu-west-1")


def _get_cors_headers():
    """Get standard CORS headers for all responses."""
    return {
        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }


def _create_error_response(status_code, error_message):
    """Create standardized error response."""
    return {
        "statusCode": status_code,
        "headers": _get_cors_headers(),
        "body": json.dumps({"error": error_message})
    }


def _upload_image_to_s3(image_data, user_id, draft_id):
    """Upload image to S3 for draft storage."""
    try:
        # Create unique filename for draft image
        image_filename = f"drafts/{user_id}/{draft_id}/{uuid.uuid4().hex}.jpg"
        s3_bucket = os.environ.get('S3_BUCKET', 'marktplaatser-images')
        
        s3.put_object(
            Bucket=s3_bucket,
            Key=image_filename,
            Body=image_data,
            ContentType='image/jpeg',
            ACL='public-read'
        )
        
        image_url = f"https://{s3_bucket}.s3.amazonaws.com/{image_filename}"
        print(f"Uploaded draft image to S3: {image_filename}")
        return image_url
        
    except Exception as e:
        print(f"Error uploading image to S3: {str(e)}")
        return None


def lambda_handler(event, context):
    """Main Lambda handler for uploading images to existing drafts."""
    try:
        # Handle CORS preflight
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": _get_cors_headers(),
                "body": ""
            }
        
        # Parse path parameters
        draft_id = event.get("pathParameters", {}).get("draftId")
        if not draft_id:
            return _create_error_response(400, "Draft ID is required")
        
        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}
        internal_user_id = query_params.get("user_id")
        if not internal_user_id:
            return _create_error_response(400, "user_id query parameter is required")
        
        # Parse request body
        try:
            body = json.loads(event["body"])
            image_base64 = body["image"]
            image_data = base64.b64decode(image_base64)
        except Exception as e:
            return _create_error_response(400, f"Invalid request format: {str(e)}")
        
        # Resolve user identity
        try:
            access_token = get_user_token(internal_user_id)
            marktplaats_user_id = get_marktplaats_user_id(access_token)
            print(f"Resolved internal user {internal_user_id} to Marktplaats user {marktplaats_user_id}")
        except Exception as e:
            print(f"Failed to resolve Marktplaats user ID: {str(e)}")
            return _create_error_response(401, f"Could not resolve user identity: {str(e)}")
        
        # Verify draft exists and user owns it
        try:
            draft = get_draft(draft_id, marktplaats_user_id)
            if not draft:
                return _create_error_response(404, "Draft not found or not owned by user")
        except Exception as e:
            return _create_error_response(500, f"Error retrieving draft: {str(e)}")
        
        # Check current image count (max 3)
        current_images = draft.images or []
        if len(current_images) >= 3:
            return _create_error_response(400, "Draft already has maximum number of images (3)")
        
        # Upload image to S3
        image_url = _upload_image_to_s3(image_data, marktplaats_user_id, draft_id)
        if not image_url:
            return _create_error_response(500, "Failed to upload image to S3")
        
        # Update draft with new image URL
        try:
            updated_images = current_images + [image_url]
            update_draft(draft_id, marktplaats_user_id, {"images": updated_images})
            print(f"Added image to draft {draft_id}. Total images: {len(updated_images)}")
        except Exception as e:
            return _create_error_response(500, f"Failed to update draft: {str(e)}")
        
        # Return success response
        return {
            "statusCode": 200,
            "headers": _get_cors_headers(),
            "body": json.dumps({
                "imageUrl": image_url,
                "totalImages": len(updated_images),
                "message": "Image uploaded successfully"
            })
        }
        
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return _create_error_response(500, str(e))