import json
import os
import uuid

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .marktplaats_auth import exchange_code_for_token, store_user_tokens


def lambda_handler(event, context):
    """
    Handle OAuth callback from Marktplaats authorization.
    
    Expected query parameters:
    - code: Authorization code
    - state: Optional state parameter for CSRF protection
    """
    
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        
        authorization_code = query_params.get('code')
        state = query_params.get('state')
        error = query_params.get('error')
        
        # Check for authorization errors
        if error:
            error_description = query_params.get('error_description', 'Unknown error')
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "text/html"
                },
                "body": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authorization Failed</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h1>❌ Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>Description: {error_description}</p>
                    <a href="/">Try again</a>
                </body>
                </html>
                """
            }
        
        # Check for authorization code
        if not authorization_code:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "text/html"
                },
                "body": """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Missing Authorization Code</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h1>❌ Missing Authorization Code</h1>
                    <p>No authorization code received from Marktplaats.</p>
                    <a href="/">Try again</a>
                </body>
                </html>
                """
            }
        
        # Build redirect URI (same as used in authorization request)
        request_context = event.get('requestContext', {})
        domain_name = request_context.get('domainName', 'localhost')
        stage = request_context.get('stage', 'dev')
        
        # Use HTTPS for API Gateway
        if domain_name == 'localhost':
            redirect_uri = "http://localhost:3000/oauth/callback"
        else:
            redirect_uri = f"https://{domain_name}/{stage}/oauth/callback"
        
        # Exchange authorization code for access token
        try:
            token_data = exchange_code_for_token(authorization_code, redirect_uri)
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "text/html"
                },
                "body": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Token Exchange Failed</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h1>❌ Token Exchange Failed</h1>
                    <p>Failed to exchange authorization code for access token.</p>
                    <p>Error: {str(e)}</p>
                    <a href="/">Try again</a>
                </body>
                </html>
                """
            }
        
        # Generate a simple user ID (in production, this should be from Marktplaats user info)
        user_id = state if state else str(uuid.uuid4())
        
        # Store user tokens
        try:
            store_user_tokens(user_id, token_data)
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "text/html"
                },
                "body": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Token Storage Failed</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h1>❌ Token Storage Failed</h1>
                    <p>Failed to store access token.</p>
                    <p>Error: {str(e)}</p>
                    <a href="/">Try again</a>
                </body>
                </html>
                """
            }
        
        # Success response with user ID for testing
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html"
            },
            "body": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Successful</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <script>
                    // Store user ID in localStorage for the frontend
                    localStorage.setItem('marktplaats_user_id', '{user_id}');
                    
                    // Auto-redirect to main app after 3 seconds
                    setTimeout(() => {{
                        window.location.href = '/';
                    }}, 3000);
                </script>
            </head>
            <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                <h1>✅ Authorization Successful!</h1>
                <p>You have successfully authorized the application.</p>
                <p>User ID: <code>{user_id}</code></p>
                <p>You can now create advertisements on Marktplaats.</p>
                <p>Redirecting back to the main application...</p>
                <a href="/">Continue to app</a>
            </body>
            </html>
            """
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }