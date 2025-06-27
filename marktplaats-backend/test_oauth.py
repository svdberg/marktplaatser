#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from marktplaats_backend.marktplaats_auth import get_authorization_url
import json

if __name__ == "__main__":
    try:
        # Test authorization URL generation
        redirect_uri = "https://a6tudg4znk.execute-api.eu-west-1.amazonaws.com/dev/oauth/callback"
        auth_url = get_authorization_url(redirect_uri, state="test-user-123")
        
        print("✅ OAuth authorization URL generated successfully:")
        print(f"🔗 {auth_url}")
        print()
        print("To test the complete OAuth flow:")
        print("1. Open the URL above in your browser")
        print("2. Log in to Marktplaats and authorize the application")
        print("3. You'll be redirected to the callback URL")
        print("4. Check the DynamoDB table for stored tokens")
        
    except Exception as e:
        print(f"❌ Failed to generate authorization URL: {e}")
        sys.exit(1)