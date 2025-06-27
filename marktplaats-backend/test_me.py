#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from marktplaats_backend.marktplaats_ads_api import get_me
import json

if __name__ == "__main__":
    try:
        user_info = get_me()
        print("✅ Successfully retrieved user information:")
        print(json.dumps(user_info, indent=2))
    except Exception as e:
        print(f"❌ Failed to get user information: {e}")
        sys.exit(1)