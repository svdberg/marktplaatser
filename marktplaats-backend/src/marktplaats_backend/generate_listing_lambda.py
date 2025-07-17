import json
import os
import base64
import boto3
import uuid
from datetime import datetime

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'
from .bedrock_utils import generate_listing_with_claude_vision
from .bedrock_rag_utils import generate_listing_with_claude_vision_rag
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


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        image_data = base64.b64decode(body["image"])
        internal_user_id = body.get("user_id")
        postcode = body.get("postcode", "1000AA")  # Default postcode if not provided
        
        # Validate required parameters
        if not internal_user_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "user_id is required"})
            }
        
        # Resolve to Marktplaats user ID for consistent draft storage
        try:
            access_token = get_user_token(internal_user_id)
            marktplaats_user_id = get_marktplaats_user_id(access_token)
            print(f"Resolved internal user {internal_user_id} to Marktplaats user {marktplaats_user_id}")
        except Exception as e:
            print(f"Failed to resolve Marktplaats user ID: {str(e)}")
            return {
                "statusCode": 401,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": f"Could not resolve user identity: {str(e)}"})
            }

        # Extract labels and text using Rekognition for additional context
        labels, text = extract_labels_and_text(image_data)

        # Try RAG approach first if Knowledge Base is configured
        knowledge_base_id = os.environ.get('TAXONOMY_KNOWLEDGE_BASE_ID')
        
        if knowledge_base_id:
            print(f"🚀 Using RAG with Knowledge Base: {knowledge_base_id}")
            # Generate listing with RAG - no expensive API calls!
            listing_data = generate_listing_with_claude_vision_rag(
                image_data=image_data,
                rekognition_labels=labels,
                rekognition_text=text,
                knowledge_base_id=knowledge_base_id
            )
        else:
            print("⚠️  Falling back to traditional approach - no Knowledge Base configured")
            # Fallback to expensive API approach
            cats = fetch_marktplaats_categories()
            flat = flatten_categories(cats)
            listing_data = generate_listing_with_claude_vision(
                image_data=image_data,
                rekognition_labels=labels,
                rekognition_text=text,
                available_categories=flat
            )

        # Handle category matching based on approach used
        if knowledge_base_id and 'categoryId' in listing_data:
            # RAG already provided categoryId, use it directly
            category_match = {
                'categoryId': listing_data['categoryId'],
                'match': listing_data.get('category', '')
            }
            print(f"✅ RAG provided category: {category_match}")
        else:
            # Traditional approach - need to match category name
            category_match = match_category_name(listing_data.get("category", ""), flat)
            if not category_match:
                return {
                    "statusCode": 400,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "POST,OPTIONS"
                    },
                    "body": json.dumps({
                        "error": "Could not match category", 
                        "suggested_category": listing_data.get("category", "")
                    })
                }

        # Map AI attributes to Marktplaats attributes
        try:
            # For RAG approach, fetch categories only when needed for attributes
            if not knowledge_base_id:
                # We already have flat categories from traditional approach
                mp_attributes = fetch_category_attributes(category_match["categoryId"], flat)
            else:
                # RAG approach - fetch categories just for attribute mapping
                cats = fetch_marktplaats_categories()
                flat = flatten_categories(cats)
                mp_attributes = fetch_category_attributes(category_match["categoryId"], flat)

            mapped_attributes = map_ai_attributes_to_marktplaats(
                listing_data.get("attributes", {}),
                mp_attributes,
            )
        except ValueError as e:
            print(f"No attributes mapped (category doesn't support attributes): {e}")
            # Category doesn't support attributes (not level 2)
            mapped_attributes = []
        except Exception as e:
            print(f"Error fetching/mapping attributes: {e}")
            # On any other error, continue without attributes
            mapped_attributes = []

        print(f"🔍 Mapped attributes: {mapped_attributes}")

        # Validate and sanitize price estimation
        estimated_price = listing_data.get("estimatedPrice")
        price_range = listing_data.get("priceRange")
        price_confidence = listing_data.get("priceConfidence")
        
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

        # Upload image to S3 for draft storage
        image_filename = f"drafts/{marktplaats_user_id}/{uuid.uuid4().hex}.jpg"
        s3_bucket = os.environ.get('S3_BUCKET', 'marktplaatser-images')
        
        try:
            s3.put_object(
                Bucket=s3_bucket,
                Key=image_filename,
                Body=image_data,
                ContentType='image/jpeg',
                ACL='public-read'  # Make draft images publicly readable
            )
            
            # Generate public S3 URL (no presigned URL needed)
            image_url = f"https://{s3_bucket}.s3.amazonaws.com/{image_filename}"
            
            print(f"Uploaded draft image to S3: {image_filename}")
            
        except Exception as e:
            print(f"Error uploading image to S3: {str(e)}")
            # Continue without image if upload fails
            image_url = None

        # Create price model for the draft
        price_model = {}
        if estimated_price is not None:
            price_model = {
                "modelType": "fixed",
                "askingPrice": estimated_price  # Store in euros, convert to cents when publishing
            }

        # Build AI result for draft creation
        ai_result = {
            "title": listing_data["title"],
            "description": listing_data["description"],
            "categoryId": category_match["categoryId"],
            "categoryName": category_match["match"],
            "attributes": mapped_attributes,
            "priceModel": price_model
        }
        
        # Create draft listing and store in DynamoDB
        draft = create_draft_from_ai_generation(
            user_id=marktplaats_user_id,
            ai_result=ai_result,
            image_urls=[image_url] if image_url else [],
            postcode=postcode
        )
        
        # Return draft information with additional AI insights
        response_data = {
            "draftId": draft.draft_id,
            "title": draft.title,
            "description": draft.description,
            "categoryId": draft.category_id,
            "categoryName": draft.category_name,
            "estimatedPrice": estimated_price,
            "priceRange": price_range,
            "priceConfidence": price_confidence,
            "message": "Draft listing created successfully! You can edit it in the Drafts section before publishing."
        }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps(response_data)
        }

    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }
