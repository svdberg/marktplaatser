import json
import os

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .marktplaats_ads_api import get_user_advertisement_images


def lambda_handler(event, context):
    """
    Lambda function to get images for a specific advertisement.
    
    Expected event format:
    - GET /advertisement-images/{id}?user_id={user_id}
    
    Returns images array with URL, width, height, etc.
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
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": json.dumps({"error": "advertisement_id path parameter is required"})
            }
        
        if not user_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": json.dumps({"error": "user_id query parameter is required"})
            }
        
        print(f"Getting images for advertisement {advertisement_id} for user {user_id} via {http_method}")
        
        # Handle OPTIONS preflight request
        if http_method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": ""
            }
        
        if http_method == 'GET':
            try:
                # Get advertisement images
                images = get_user_advertisement_images(advertisement_id, user_id)
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,OPTIONS"
                    },
                    "body": json.dumps(images)
                }
                
            except ValueError as e:
                # Handle authentication/token errors and validation errors
                print(f"Authentication or validation error for user {user_id}: {str(e)}")
                status_code = 401 if "token" in str(e).lower() else 400
                return {
                    "statusCode": status_code,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,OPTIONS"
                    },
                    "body": json.dumps({"error": str(e)})
                }
        else:
            return {
                "statusCode": 405,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": json.dumps({"error": f"Method {http_method} not allowed"})
            }
                
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }