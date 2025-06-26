import json
import os

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

from .category_matcher import fetch_marktplaats_categories, flatten_categories


def lambda_handler(event, context):
    """
    Lambda handler for fetching Marktplaats categories.
    
    Returns all level 2 categories that support attributes, formatted for frontend dropdown/autocomplete.
    """
    
    # Handle CORS preflight OPTIONS requests
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": ""
        }
    
    try:
        # Fetch all categories
        categories = fetch_marktplaats_categories()
        flat_categories = flatten_categories(categories)
        
        # Filter for level 2 categories (contain exactly one " > ")
        level_2_categories = [
            cat for cat in flat_categories 
            if cat["name"].count(" > ") == 1
        ]
        
        # Format for frontend dropdown/autocomplete
        formatted_categories = []
        for cat in level_2_categories:
            formatted_categories.append({
                "id": cat["id"],
                "name": cat["name"],
                "displayName": cat["name"].replace(" > ", " → "),  # Make it prettier
                "level1": cat["name"].split(" > ")[0],
                "level2": cat["name"].split(" > ")[1]
            })
        
        # Sort by category name for better UX
        formatted_categories.sort(key=lambda x: x["name"])
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps({
                "categories": formatted_categories,
                "total": len(formatted_categories)
            })
        }
        
    except Exception as e:
        print(f"Error fetching categories: {e}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps({
                "error": "Failed to fetch categories",
                "details": str(e)
            })
        }