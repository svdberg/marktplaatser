import boto3
import json
import uuid
import base64
from rekognition_utils import analyze_image_with_rekognition
from bedrock_utils import generate_listing_with_bedrock
from s3_utils import upload_image_to_s3

s3_bucket = "marktplaatser-images"
rekognition_client = boto3.client("rekognition")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        image_data = base64.b64decode(body["image_base64"])

        # Upload to S3 (optional, for later use or debugging)
        image_key = f"uploads/{str(uuid.uuid4())}.jpg"
        upload_image_to_s3(image_data, s3_bucket, image_key)

        # Run Rekognition using inline bytes
        labels, text = analyze_image_with_rekognition(rekognition_client, image_bytes=image_data)

        # Compose prompt for LLM
        listing_data = generate_listing_with_bedrock(labels, text)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "title": listing_data["title"],
                "description": listing_data["description"],
                "category": listing_data["category"],
                "attributes": listing_data["attributes"]
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
