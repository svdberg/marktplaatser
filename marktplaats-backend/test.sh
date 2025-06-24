#!/bin/bash

set -e

if [ -z "$API_URL" ]; then
  echo "Please set the API_URL environment variable."
  exit 1
fi

IMAGE_FILE=${1:-sample.jpg}

if [ ! -f "$IMAGE_FILE" ]; then
  echo "Image file '$IMAGE_FILE' not found."
  exit 1
fi

BASE64_IMAGE=$(base64 -i "$IMAGE_FILE" | tr -d '\n')

echo "Sending request to Lambda..."

curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"${BASE64_IMAGE}\"}" | jq
