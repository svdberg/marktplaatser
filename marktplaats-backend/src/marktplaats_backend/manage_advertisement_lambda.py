import json
import os

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .marktplaats_ads_api import get_user_advertisement, update_user_advertisement, delete_user_advertisement, toggle_advertisement_reserved_status


def lambda_handler(event, context):
    """
    Lambda function to manage (get/update/delete) advertisements for a specific user.
    
    Expected event formats:
    - GET /manage-advertisement/{id}:    Get advertisement details
    - PUT /manage-advertisement/{id}:    Update advertisement
    - DELETE /manage-advertisement/{id}: Delete advertisement
    
    All operations require user_id query parameter for authentication.
    """
    try:
        # Extract HTTP method and path parameters
        http_method = event.get('httpMethod', '').upper()
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        
        advertisement_id = path_params.get('id')
        user_id = query_params.get('user_id')
        
        # Validate required parameters
        if not advertisement_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                },
                "body": json.dumps({"error": "advertisement_id path parameter is required"})
            }
        
        if not user_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                },
                "body": json.dumps({"error": "user_id query parameter is required"})
            }
        
        print(f"Managing advertisement {advertisement_id} for user {user_id} via {http_method}")
        
        # Handle OPTIONS preflight request
        if http_method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                },
                "body": ""
            }
        
        try:
            if http_method == 'GET':
                # Get advertisement details
                advertisement = get_user_advertisement(advertisement_id, user_id)
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                    },
                    "body": json.dumps(advertisement)
                }
                
            elif http_method == 'PATCH':
                # Update advertisement
                if not event.get('body'):
                    return {
                        "statusCode": 400,
                        "headers": {
                            "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                            "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                        },
                        "body": json.dumps({"error": "Request body is required for updates"})
                    }
                
                try:
                    body = json.loads(event['body'])
                    print(f"PATCH request body received: {body}")
                except json.JSONDecodeError:
                    return {
                        "statusCode": 400,
                        "headers": {
                            "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                            "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                        },
                        "body": json.dumps({"error": "Invalid JSON in request body"})
                    }
                
                # Extract update fields
                title = body.get('title')
                description = body.get('description')
                price_model = body.get('priceModel')
                attributes = body.get('attributes')
                reserved = body.get('reserved')
                asking_price = body.get('askingPrice')  # For unreserving
                
                print(f"Extracted fields:")
                print(f"  - title: {title}")
                print(f"  - description: {description}")
                print(f"  - reserved: {reserved} (type: {type(reserved)})")
                print(f"  - asking_price: {asking_price}")
                
                # Validate title length if provided
                if title is not None and len(title) > 60:
                    return {
                        "statusCode": 400,
                        "headers": {
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                            "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                        },
                        "body": json.dumps({"error": "Title must be 60 characters or less"})
                    }
                
                # Handle reserved status separately if provided
                reserved_result = None
                if reserved is not None:
                    if not isinstance(reserved, bool):
                        return {
                            "statusCode": 400,
                            "headers": {
                                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                                "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                            },
                            "body": json.dumps({"error": "Reserved status must be a boolean value"})
                        }
                    
                    # When unreserving (reserved=False) and no explicit asking_price provided,
                    # try to use asking price from priceModel if available
                    effective_asking_price = asking_price
                    if not reserved and not asking_price and price_model and 'askingPrice' in price_model:
                        effective_asking_price = price_model['askingPrice']
                        print(f"Using askingPrice from priceModel for unreserving: {effective_asking_price}")
                    
                    # Update reserved status first
                    reserved_result = toggle_advertisement_reserved_status(advertisement_id, user_id, reserved, effective_asking_price)
                    
                    # If only reserved status was updated, return the result
                    if all(field is None for field in [title, description, price_model, attributes]):
                        return {
                            "statusCode": 200,
                            "headers": {
                                "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                                "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                            },
                            "body": json.dumps(reserved_result)
                        }
                
                # Update other fields if provided
                other_fields_result = None
                if any(field is not None for field in [title, description, price_model, attributes]):
                    other_fields_result = update_user_advertisement(
                        advertisement_id,
                        user_id,
                        title=title,
                        description=description,
                        price_model=price_model,
                        attributes=attributes
                    )
                
                # Check if any updates were made
                if reserved_result is None and other_fields_result is None:
                    return {
                        "statusCode": 400,
                        "headers": {
                            "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                            "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                        },
                        "body": json.dumps({"error": "At least one field must be provided for update"})
                    }
                
                # Return the most relevant result (prefer other fields result over reserved result)
                final_result = other_fields_result if other_fields_result is not None else reserved_result
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                    },
                    "body": json.dumps(final_result)
                }
                
            elif http_method == 'DELETE':
                # Delete advertisement
                result = delete_user_advertisement(advertisement_id, user_id)
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                    },
                    "body": json.dumps(result)
                }
                
            else:
                return {
                    "statusCode": 405,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                    },
                    "body": json.dumps({"error": f"Method {http_method} not allowed"})
                }
                
        except ValueError as e:
            # Handle authentication/token errors and validation errors
            print(f"Authentication or validation error for user {user_id}: {str(e)}")
            status_code = 401 if "token" in str(e).lower() else 400
            return {
                "statusCode": status_code,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,PATCH,DELETE,OPTIONS"
                },
                "body": json.dumps({"error": str(e)})
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
                "Access-Control-Allow-Methods": "GET,PUT,DELETE,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }