import json
import os
import uuid

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .marktplaats_auth import get_authorization_url


def lambda_handler(event, context):
    """
    Initiate OAuth authorization flow by redirecting to Marktplaats.
    
    Query parameters:
    - user_id: Optional user identifier for state tracking
    """
    
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        user_id = query_params.get('user_id', str(uuid.uuid4()))
        
        # Build redirect URI
        request_context = event.get('requestContext', {})
        domain_name = request_context.get('domainName', 'localhost')
        stage = request_context.get('stage', 'dev')
        
        # Use HTTPS for API Gateway
        if domain_name == 'localhost':
            redirect_uri = "http://localhost:3000/oauth/callback"
        else:
            redirect_uri = f"https://{domain_name}/{stage}/oauth/callback"
        
        # Generate authorization URL
        auth_url = get_authorization_url(
            redirect_uri=redirect_uri,
            state=user_id  # Use user_id as state for tracking
        )
        
        # Redirect user to Marktplaats authorization
        return {
            "statusCode": 302,
            "headers": {
                "Location": auth_url,
                "Cache-Control": "no-cache"
            },
            "body": ""
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Failed to initiate authorization",
                "details": str(e)
            })
        }