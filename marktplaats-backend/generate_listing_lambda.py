import json
import os
import base64
import boto3
from bedrock_utils import generate_listing_with_bedrock
from rekognition_utils import extract_labels_and_text
from category_matcher import (
    match_category_name,
    fetch_marktplaats_categories,
    flatten_categories,
)
from attribute_mapper import (
    fetch_category_attributes,
    map_ai_attributes_to_marktplaats,
)

s3 = boto3.client("s3")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        image_data = base64.b64decode(body["image"])

        # Extract labels and text using Rekognition
        labels, text = extract_labels_and_text(image_data)

        # Generate listing with Claude
        listing_data = generate_listing_with_bedrock(labels, text)

        cats = fetch_marktplaats_categories()
        flat = flatten_categories(cats)

        # Match category
        category_match = match_category_name(listing_data.get("category", ""), flat)
        if not category_match:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Could not match category"})
            }

        # Map AI attributes to Marktplaats attributes
        mp_attributes = fetch_category_attributes(category_match["categoryId"])
        mapped_attributes = map_ai_attributes_to_marktplaats(
            listing_data.get("attributes", {}),
            mp_attributes,
        )

        # Build listing result
        listing = {
            "title": listing_data["title"],
            "description": listing_data["description"],
            "categoryId": category_match["categoryId"],
            "categoryName": category_match["match"],
            "attributes": mapped_attributes,
        }

        return {
            "statusCode": 200,
            "body": json.dumps(listing)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
