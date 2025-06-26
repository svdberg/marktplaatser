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
                "body": json.dumps({"error": "listingData is required"})
            }
            
        if not image_base64:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "image is required"})
            }
            
        if not user_details:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "userDetails is required"})
            }
            
        if not user_id:
            return {
                "statusCode": 400,
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
            
            advertisement_id = ad_response.get("id")
            if not advertisement_id:
                raise ValueError("No advertisement ID returned")
                
            print(f"Advertisement created with ID: {advertisement_id}")
            
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Failed to create advertisement",
                    "details": str(e)
                })
            }
        
        # Step 4: Upload image to advertisement
        print("Uploading image to advertisement...")
        try:
            image_response = upload_advertisement_images(
                advertisement_id=advertisement_id,
                image_urls=[image_url]
            )
            print(f"Image upload response: {image_response}")
            
        except Exception as e:
            # Advertisement was created but image upload failed
            print(f"Image upload failed: {e}")
            return {
                "statusCode": 207,  # Multi-status: partial success
                "body": json.dumps({
                    "message": "Advertisement created but image upload failed",
                    "advertisementId": advertisement_id,
                    "imageError": str(e),
                    "advertisement": ad_response
                })
            }
        
        # Step 5: Get final advertisement details
        try:
            final_ad = get_advertisement(advertisement_id)
        except Exception:
            # Use the creation response if we can't fetch updated details
            final_ad = ad_response
        
        # Success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Advertisement created successfully",
                "advertisementId": advertisement_id,
                "imageUrl": image_url,
                "advertisement": final_ad,
                "imageUpload": image_response
            })
        }
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }