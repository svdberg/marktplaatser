import json
import os

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .marktplaats_ads_api import list_user_advertisements


def lambda_handler(event, context):
    """
    Lambda function to list advertisements for a specific user.
    
    Expected event format:
    - GET /list-advertisements
    - Query parameters: user_id (required), offset (optional), limit (optional)
    """
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        
        if not user_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": json.dumps({"error": "user_id parameter is required"})
            }
        
        # Parse optional pagination parameters
        offset = None
        limit = None
        
        if 'offset' in query_params:
            try:
                offset = int(query_params['offset'])
            except ValueError:
                return {
                    "statusCode": 400,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,OPTIONS"
                    },
                    "body": json.dumps({"error": "offset must be an integer"})
                }
        
        if 'limit' in query_params:
            try:
                limit = int(query_params['limit'])
                if limit < 1 or limit > 100:
                    raise ValueError("limit must be between 1 and 100")
            except ValueError as e:
                return {
                    "statusCode": 400,
                    "headers": {
                        "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "GET,OPTIONS"
                    },
                    "body": json.dumps({"error": str(e)})
                }
        
        print(f"Listing advertisements for user: {user_id}, offset: {offset}, limit: {limit}")
        
        # Call the API function
        try:
            advertisements = list_user_advertisements(user_id, offset, limit)
            
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": json.dumps(advertisements)
            }
            
        except ValueError as e:
            # Handle authentication/token errors
            print(f"Authentication error for user {user_id}: {str(e)}")
            return {
                "statusCode": 401,
                "headers": {
                    "Access-Control-Allow-Origin": "http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                    "Access-Control-Allow-Methods": "GET,OPTIONS"
                },
                "body": json.dumps({"error": "Authentication failed", "details": str(e)})
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
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }