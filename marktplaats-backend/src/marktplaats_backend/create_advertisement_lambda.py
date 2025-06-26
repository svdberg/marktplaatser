import json
import os
import base64

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .s3_image_utils import upload_image_to_s3, verify_image_accessible
from .marktplaats_ads_api import (
    create_advertisement,
    upload_advertisement_images,
    validate_advertisement_data,
    get_advertisement
)
from .attribute_mapper import fetch_category_attributes
from .category_matcher import fetch_marktplaats_categories, flatten_categories


def lambda_handler(event, context):
    """
    Lambda handler for creating Marktplaats advertisements.
    
    Expected input:
    {
        "listingData": {
            "title": "...",
            "description": "...", 
            "categoryId": 123,
            "attributes": [...]
        },
        "image": "base64_encoded_image",
        "userDetails": {
            "postcode": "1234AB",
            "priceModel": {
                "modelType": "fixed",
                "askingPrice": 150
            }
        }
    }
    """
    
    # Handle CORS preflight OPTIONS requests
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": ""
        }
    
    try:
        # Parse request body
        body = json.loads(event["body"])
        
        # Extract required data
        listing_data = body.get("listingData", {})
        image_base64 = body.get("image")
        user_details = body.get("userDetails", {})
        user_id = body.get("userId")
        
        # Validate input
        if not listing_data:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "listingData is required"})
            }
            
        if not image_base64:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "image is required"})
            }
            
        if not user_details:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "userDetails is required"})
            }
            
        if not user_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "userId is required for authorization"})
            }
        
        # Extract user details
        postcode = user_details.get("postcode")
        price_model = user_details.get("priceModel")
        
        # Validate advertisement data
        validation_errors = validate_advertisement_data(
            listing_data, postcode, price_model
        )
        
        if validation_errors:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({
                    "error": "Validation failed",
                    "details": validation_errors
                })
            }
        
        # Validate category-specific attributes
        category_id = listing_data.get("categoryId")
        if category_id:
            try:
                # Fetch category attributes to check requirements
                cats = fetch_marktplaats_categories()
                flat = flatten_categories(cats)
                category_attributes = fetch_category_attributes(category_id, flat)
                
                # Check if all required attributes are provided
                required_attrs = [
                    attr for attr in category_attributes 
                    if attr.get("required", False)
                ]
                
                provided_attr_keys = [
                    attr.get("key") for attr in listing_data.get("attributes", [])
                ]
                
                missing_required = [
                    attr["key"] for attr in required_attrs
                    if attr["key"] not in provided_attr_keys
                ]
                
                if missing_required:
                    return {
                        "statusCode": 400,
                        "headers": {
                            "Access-Control-Allow-Origin": "http://localhost:3000",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                            "Access-Control-Allow-Methods": "POST,OPTIONS"
                        },
                        "body": json.dumps({
                            "error": "Missing required category attributes",
                            "missingAttributes": missing_required
                        })
                    }
                    
            except ValueError as e:
                # Category doesn't support attributes (level 1) - continue without validation
                print(f"Category attribute validation skipped: {e}")
        
        # Step 1: Upload image to S3
        print("Uploading image to S3...")
        try:
            image_url = upload_image_to_s3(image_base64)
            print(f"Image uploaded to: {image_url}")
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({
                    "error": "Failed to upload image",
                    "details": str(e)
                })
            }
        
        # Step 2: Verify image is accessible (optional for pre-signed URLs)
        print("Verifying image accessibility...")
        image_accessible = verify_image_accessible(image_url)
        if not image_accessible:
            print("Warning: Image accessibility check failed, but continuing with pre-signed URL")
            # Continue anyway - pre-signed URLs should work for Marktplaats API
        
        # Step 3: Create advertisement
        print("Creating advertisement...")
        try:
            ad_response = create_advertisement(
                title=listing_data["title"],
                description=listing_data["description"],
                category_id=category_id,
                postcode=postcode,
                price_model=price_model,
                attributes=listing_data.get("attributes", []),
                user_id=user_id
            )
            
            advertisement_id = ad_response.get("itemId") or ad_response.get("id")
            if not advertisement_id:
                raise ValueError(f"No advertisement ID returned. Response keys: {list(ad_response.keys())}")
                
            print(f"Advertisement created with ID: {advertisement_id}")
            
            # Step 4: Upload image to advertisement (optional - if this fails, ad still exists)
            try:
                print("Uploading image to advertisement...")
                upload_response = upload_advertisement_images(advertisement_id, [image_url], user_id=user_id)
                print(f"Image upload successful: {upload_response}")
            except Exception as upload_error:
                print(f"Warning: Image upload failed but advertisement was created: {upload_error}")
                # Continue - we'll return success even if image upload fails
            
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({
                    "error": "Failed to create advertisement",
                    "details": str(e)
                })
            }
        
        # Return success immediately - image upload will be handled separately
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({
                "message": "Advertisement created successfully",
                "advertisementId": advertisement_id,
                "imageUrl": image_url,
                "title": ad_response.get("title"),
                "status": ad_response.get("status"),
                "websiteLink": ad_response.get("_links", {}).get("mp:advertisement-website-link", {}).get("href"),
                "note": "Image upload will be processed separately due to timeout constraints"
            })
        }
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }