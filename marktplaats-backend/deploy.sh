#!/bin/bash

set -e

# Set your bucket name here (must be globally unique)
BUCKET_NAME="marktplaatser-images"

# Create S3 bucket (skip if it already exists)
echo "Creating S3 bucket if needed: $BUCKET_NAME"
aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1 \
  2>/dev/null || echo "Bucket may already exist."

# Deploy with Serverless
echo "Deploying with Serverless..."
serverless deploy

# Get endpoint and save to file
echo ""
echo "Getting endpoint..."
ENDPOINT=$(serverless info 2>&1 | grep -o 'https://[^[:space:]]*')
echo "$ENDPOINT" > endpoint.txt
echo "Endpoint saved to endpoint.txt: $ENDPOINT"

# Output endpoint
echo ""
echo "Deployment complete. Endpoint: $ENDPOINT"
