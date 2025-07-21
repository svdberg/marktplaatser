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
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
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
        image_base64 = body.get("image")  # Single image (backward compatibility)
        images_base64 = body.get("images", [])  # Multiple images (new format)
        user_details = body.get("userDetails", {})
        user_id = body.get("userId")
        category_override = body.get("categoryOverride")  # Optional category override
        
        # Validate input
        if not listing_data:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "listingData is required"})
            }
            
        # Validate at least one image is provided (backward compatibility)
        if not image_base64 and not images_base64:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "At least one image is required (image or images)"})
            }
            
        if not user_details:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "userDetails is required"})
            }
            
        if not user_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"error": "userId is required for authorization"})
            }
        
        # Extract user details
        postcode = user_details.get("postcode")
        price_model = user_details.get("priceModel")
        
        # Convert price from euros to cents (Marktplaats API expects cents)
        if price_model and "askingPrice" in price_model:
            # Convert euros to cents (multiply by 100)
            euro_price = price_model["askingPrice"]
            price_model["askingPrice"] = int(euro_price * 100)
        
        # Apply category override if provided
        if category_override:
            print(f"Overriding category from {listing_data.get('categoryId')} to {category_override}")
            listing_data["categoryId"] = category_override
        
        # Validate advertisement data
        validation_errors = validate_advertisement_data(
            listing_data, postcode, price_model
        )
        
        if validation_errors:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
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
                            "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
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
        
        # Step 1: Prepare images for upload (support both single and multiple images)
        images_to_upload = []
        if images_base64:  # Multiple images provided (new format)
            images_to_upload = images_base64
        elif image_base64:  # Single image provided (backward compatibility)
            images_to_upload = [image_base64]
        
        # Step 2: Upload all images to S3
        print(f"Uploading {len(images_to_upload)} image(s) to S3...")
        image_urls = []
        try:
            for i, img_base64 in enumerate(images_to_upload):
                image_url = upload_image_to_s3(img_base64)
                image_urls.append(image_url)
                print(f"Image {i+1}/{len(images_to_upload)} uploaded to: {image_url}")
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({
                    "error": "Failed to upload images",
                    "details": str(e)
                })
            }
        
        # Step 3: Verify images are accessible (optional for pre-signed URLs)
        print("Verifying image accessibility...")
        for i, image_url in enumerate(image_urls):
            image_accessible = verify_image_accessible(image_url)
            if not image_accessible:
                print(f"Warning: Image {i+1} accessibility check failed, but continuing with pre-signed URL")
                # Continue anyway - pre-signed URLs should work for Marktplaats API
        
        # Step 4: Create advertisement
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
            
            # Step 5: Upload all images to advertisement (optional - if this fails, ad still exists)
            if image_urls:
                try:
                    print(f"Uploading {len(image_urls)} image(s) to advertisement...")
                    upload_response = upload_advertisement_images(advertisement_id, image_urls, user_id=user_id)
                    print(f"Image upload successful: {upload_response}")
                except Exception as upload_error:
                    print(f"Warning: Image upload failed but advertisement was created: {upload_error}")
                    # Continue - we'll return success even if image upload fails
            
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
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
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({
                "message": "Advertisement created successfully",
                "advertisementId": advertisement_id,
                "imageUrls": image_urls,
                "imageCount": len(image_urls),
                "title": ad_response.get("title"),
                "status": ad_response.get("status"),
                "websiteLink": ad_response.get("_links", {}).get("mp:advertisement-website-link", {}).get("href"),
                "note": f"{len(image_urls)} image(s) uploaded successfully"
            })
        }
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
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
                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }