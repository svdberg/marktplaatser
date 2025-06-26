#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from marktplaats_backend.marktplaats_auth import exchange_code_for_token
import json

if __name__ == "__main__":
    # Test with the actual values from the callback
    authorization_code = "509ec8ed-064b-49"  # This might be truncated
    redirect_uri = "https://a6tudg4znk.execute-api.eu-west-1.amazonaws.com/dev/oauth/callback"
    
    try:
        print("Testing token exchange...")
        print(f"Code: {authorization_code}")
        print(f"Redirect URI: {redirect_uri}")
        
        token_data = exchange_code_for_token(authorization_code, redirect_uri)
        print("✅ Token exchange successful!")
        print(f"Token data: {json.dumps(token_data, indent=2)}")
        
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()