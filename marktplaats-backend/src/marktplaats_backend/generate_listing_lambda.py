import json
import os
import base64
import boto3

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

s3 = boto3.client("s3", region_name="eu-west-1")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        image_data = base64.b64decode(body["image"])

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

        # Build listing result
        listing = {
            "title": listing_data["title"],
            "description": listing_data["description"],
            "categoryId": category_match["categoryId"],
            "categoryName": category_match["match"],
            "attributes": mapped_attributes,
            "estimatedPrice": estimated_price,
            "priceRange": price_range,
            "priceConfidence": price_confidence
        }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps(listing)
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
