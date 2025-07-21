import json
import os
import base64
import boto3
import uuid
from datetime import datetime

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .pinecone_rag_utils import generate_listing_with_pinecone_rag

from .rekognition_utils import extract_labels_and_text
from .category_matcher import (
    match_category_name,
    fetch_marktplaats_categories,
    flatten_categories,
)
from .attribute_mapper import (
    fetch_category_attributes,
    map_ai_attributes_to_marktplaats,
)
from .draft_storage import create_draft_from_ai_generation
from .marktplaats_auth import get_marktplaats_user_id, get_user_token

s3 = boto3.client("s3", region_name="eu-west-1")


def _get_cors_headers():
    """Get standard CORS headers for all responses."""
    return {
        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }


def _create_error_response(status_code, error_message, extra_data=None):
    """Create standardized error response."""
    error_body = {"error": error_message}
    if extra_data:
        error_body.update(extra_data)
    
    return {
        "statusCode": status_code,
        "headers": _get_cors_headers(),
        "body": json.dumps(error_body)
    }


def _parse_and_validate_request(event):
    """Parse and validate the incoming request."""
    try:
        body = json.loads(event["body"])
        image_data = base64.b64decode(body["image"])
        internal_user_id = body.get("user_id")
        postcode = body.get("postcode", "1000AA")
        
        if not internal_user_id:
            return None, _create_error_response(400, "user_id is required")
            
        return {
            "image_data": image_data,
            "internal_user_id": internal_user_id,
            "postcode": postcode
        }, None
        
    except Exception as e:
        return None, _create_error_response(400, f"Invalid request format: {str(e)}")


def _resolve_marktplaats_user(internal_user_id):
    """Resolve internal user ID to Marktplaats user ID."""
    try:
        access_token = get_user_token(internal_user_id)
        marktplaats_user_id = get_marktplaats_user_id(access_token)
        print(f"Resolved internal user {internal_user_id} to Marktplaats user {marktplaats_user_id}")
        return marktplaats_user_id, None
    except Exception as e:
        print(f"Failed to resolve Marktplaats user ID: {str(e)}")
        return None, _create_error_response(401, f"Could not resolve user identity: {str(e)}")


def _find_category_match(listing_data, flat_categories):
    """Find category match using Pinecone RAG result."""
    category_id = listing_data.get("categoryId")
    category_match = None
    
    if category_id:
        # Convert category_id to int for comparison (Pinecone returns float)
        category_id_int = int(category_id) if category_id else None
        print(f"🔍 Looking for category ID: {category_id_int}")
        
        # Find the category in the flat list by ID
        for cat in flat_categories:
            cat_id = cat.get("id")
            if cat_id is not None and int(cat_id) == category_id_int:
                category_match = cat
                print(f"✅ Found category match: {category_match}")
                break
    
    if not category_match:
        return None, _create_error_response(
            400, 
            "Could not find category",
            {
                "category_id": category_id,
                "suggested_category": listing_data.get("category", "")
            }
        )
    
    print(f"✅ RAG provided category: {category_match}")
    return category_match, None


def _map_attributes(listing_data, category_match, flat_categories):
    """Map AI attributes to Marktplaats attributes."""
    try:
        # Use defensive field access for category ID
        category_id_for_attributes = category_match.get("id") or category_match.get("categoryId")
        mp_attributes = fetch_category_attributes(category_id_for_attributes, flat_categories)

        mapped_attributes = map_ai_attributes_to_marktplaats(
            listing_data.get("attributes", {}),
            mp_attributes,
        )
        return mapped_attributes
    except ValueError as e:
        print(f"No attributes mapped (category doesn't support attributes): {e}")
        return []
    except Exception as e:
        print(f"Error fetching/mapping attributes: {e}")
        return []


def _upload_image_to_s3(image_data, marktplaats_user_id):
    """Upload image to S3 for draft storage."""
    try:
        image_filename = f"drafts/{marktplaats_user_id}/{uuid.uuid4().hex}.jpg"
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


def _create_price_model(listing_data, estimated_price):
    """Create price model based on AI suggestion and estimated price."""
    suggested_pricing_model = listing_data.get("suggestedPricingModel", "fixed")
    
    if estimated_price is not None:
        if suggested_pricing_model == "bidding":
            # Create bidding model according to official API specification
            minimal_bid_amount = max(1, int(estimated_price * 0.10))
            price_model = {
                "modelType": "bidding",
                "askingPrice": estimated_price,
                "minimalBid": minimal_bid_amount
            }
            print(f"💰 Created bidding model: asking €{estimated_price}, minimal bid €{minimal_bid_amount}")
        else:
            price_model = {
                "modelType": "fixed",
                "askingPrice": estimated_price
            }
            print(f"💰 Created fixed price model: €{estimated_price}")
    else:
        # No price estimated, create basic structure
        if suggested_pricing_model == "bidding":
            price_model = {
                "modelType": "bidding",
                "askingPrice": 0,
                "minimalBid": 1
            }
        else:
            price_model = {
                "modelType": "fixed",
                "askingPrice": 0
            }
    
    return price_model, suggested_pricing_model


def _validate_and_sanitize_price(estimated_price, price_range, price_confidence):
    """Validate and sanitize price estimation data."""
    # Basic price validation - ensure reasonable bounds
    if estimated_price is not None:
        # Clamp price between €1 and €50,000
        estimated_price = max(1, min(50000, int(estimated_price)))
        
    if price_range is not None:
        # Validate price range bounds
        if isinstance(price_range, dict) and "min" in price_range and "max" in price_range:
            price_range["min"] = max(1, min(50000, int(price_range["min"])))
            price_range["max"] = max(1, min(50000, int(price_range["max"])))
            # Ensure min <= max
            if price_range["min"] > price_range["max"]:
                price_range["min"], price_range["max"] = price_range["max"], price_range["min"]
        else:
            price_range = None
    
    return estimated_price, price_range, price_confidence


def _build_response_data(draft, estimated_price, price_range, price_confidence, price_model, suggested_pricing_model):
    """Build the final response data."""
    return {
        "draftId": draft.draft_id,
        "title": draft.title,
        "description": draft.description,
        "categoryId": draft.category_id,
        "categoryName": draft.category_name,
        "estimatedPrice": estimated_price,
        "priceRange": price_range,
        "priceConfidence": price_confidence,
        "priceModel": price_model,
        "suggestedPricingModel": suggested_pricing_model,
        "message": f"Draft listing created successfully with {suggested_pricing_model} pricing model! You can edit it in the Drafts section before publishing."
    }


def lambda_handler(event, context):
    """Main Lambda handler for generating listings using Vision + Pinecone RAG."""
    try:
        # Parse and validate request
        request_data, error_response = _parse_and_validate_request(event)
        if error_response:
            return error_response
        
        # Resolve user identity
        marktplaats_user_id, error_response = _resolve_marktplaats_user(request_data["internal_user_id"])
        if error_response:
            return error_response

        # Extract image features using Rekognition
        labels, text = extract_labels_and_text(request_data["image_data"])

        # Fetch Marktplaats categories
        cats = fetch_marktplaats_categories()
        flat = flatten_categories(cats)

        # Generate listing with Pinecone RAG (Vision + vector search)
        listing_data = generate_listing_with_pinecone_rag(
            image_data=request_data["image_data"],
            rekognition_labels=labels,
            rekognition_text=text
        )

        # Find category match
        category_match, error_response = _find_category_match(listing_data, flat)
        if error_response:
            return error_response

        # Map AI attributes to Marktplaats format
        mapped_attributes = _map_attributes(listing_data, category_match, flat)
        print(f"🔍 Mapped attributes: {mapped_attributes}")

        # Validate and sanitize pricing data
        estimated_price, price_range, price_confidence = _validate_and_sanitize_price(
            listing_data.get("estimatedPrice"),
            listing_data.get("priceRange"), 
            listing_data.get("priceConfidence")
        )

        # Upload image to S3
        image_url = _upload_image_to_s3(request_data["image_data"], marktplaats_user_id)

        # Create price model
        price_model, suggested_pricing_model = _create_price_model(listing_data, estimated_price)

        # Build AI result for draft creation
        category_id_final = category_match.get("id") or category_match.get("categoryId")
        category_name_final = category_match.get("name") or category_match.get("displayName", "Unknown Category")
        
        print(f"🏷️  Final category: ID={category_id_final}, Name={category_name_final}")
        
        ai_result = {
            "title": listing_data["title"],
            "description": listing_data["description"],
            "categoryId": category_id_final,
            "categoryName": category_name_final,
            "attributes": mapped_attributes,
            "priceModel": price_model
        }
        
        # Create draft listing and store in DynamoDB
        draft = create_draft_from_ai_generation(
            user_id=marktplaats_user_id,
            ai_result=ai_result,
            image_urls=[image_url] if image_url else [],
            postcode=request_data["postcode"]
        )
        
        # Build response data
        response_data = _build_response_data(
            draft, estimated_price, price_range, price_confidence, 
            price_model, suggested_pricing_model
        )

        return {
            "statusCode": 200,
            "headers": _get_cors_headers(),
            "body": json.dumps(response_data)
        }

    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return _create_error_response(500, str(e))
