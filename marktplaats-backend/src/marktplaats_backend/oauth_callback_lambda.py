import json
import os
import uuid

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .marktplaats_auth import exchange_code_for_token, store_user_tokens, get_marktplaats_user_id


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
        
        print(f"Received query parameters: {query_params}")
        print(f"Full event: {json.dumps(event)}")
        
        authorization_code = query_params.get('code')
        state = query_params.get('state')
        error = query_params.get('error')
        
        print(f"Parsed authorization_code: {authorization_code}")
        print(f"Parsed state: {state}")
        
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
        
        # Build redirect URI (must match exactly what was used in authorization request)
        request_context = event.get('requestContext', {})
        domain_name = request_context.get('domainName', 'localhost')
        stage = request_context.get('stage', 'dev')
        
        # This must match the redirect_uri used in the authorization request
        # The authorization request uses the AWS Lambda callback URL
        if domain_name == 'localhost':
            redirect_uri = "http://localhost:8000/dev/oauth/callback"  # For local development
        else:
            # Use AWS Lambda callback URL - same as in oauth_authorize_lambda.py
            redirect_uri = f"https://{domain_name}/{stage}/oauth/callback"
        
        # Exchange authorization code for access token
        try:
            print(f"Exchanging code: {authorization_code}")
            print(f"Redirect URI: {redirect_uri}")
            token_data = exchange_code_for_token(authorization_code, redirect_uri)
            print(f"Token exchange successful: {token_data}")
        except Exception as e:
            print(f"Token exchange error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
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
        
        # Get the actual Marktplaats user ID from the access token
        try:
            user_id = get_marktplaats_user_id(token_data['access_token'])
            print(f"Got Marktplaats user ID: {user_id}")
        except Exception as e:
            print(f"Failed to get Marktplaats user ID: {str(e)}")
            # Fallback to UUID for backward compatibility
            user_id = state if state else str(uuid.uuid4())
            print(f"Using fallback user_id: {user_id}")
        
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
        
        # Get frontend domain
        frontend_domain = os.environ.get('FRONTEND_DOMAIN', 'localhost:3000')
        
        # Return HTML page that stores user_id in localStorage and redirects
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
                    console.log('OAuth callback: storing user_id in localStorage:', '{user_id}');
                    // Store user ID in localStorage for the frontend
                    localStorage.setItem('marktplaats_user_id', '{user_id}');
                    
                    // Redirect to frontend callback page with user_id in hash after short delay
                    setTimeout(() => {{
                        console.log('Redirecting to: ','{frontend_domain}/callback#user_id={user_id}');
                        window.location.href = 'http://{frontend_domain}/callback#user_id={user_id}';
                    }}, 1000);
                </script>
            </head>
            <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                <h1>✅ Authorization Successful!</h1>
                <p>Redirecting to application...</p>
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