#!/bin/bash

set -e

# API_BASE is the base URL of the deployed API Gateway.
# For backwards compatibility API_URL can also be used.
API_BASE=${API_BASE:-$API_URL}
if [ -z "$API_BASE" ]; then
  echo "Please set the API_BASE environment variable."
  exit 1
fi

IMAGE_FILE=${1:-sample.jpg}

if [ ! -f "$IMAGE_FILE" ]; then
  echo "Image file '$IMAGE_FILE' not found."
  exit 1
fi

BASE64_IMAGE=$(base64 -i "$IMAGE_FILE" | tr -d '\n')

GEN_URL="$API_BASE/generate-listing"
PLACE_URL="$API_BASE/place-listing"

echo "Calling generateListing at $GEN_URL..."

LISTING_JSON=$(curl -s -X POST "$GEN_URL" \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"${BASE64_IMAGE}\"}")

echo "$LISTING_JSON" | jq

echo "\nCalling placeListing at $PLACE_URL..."

curl -s -X POST "$PLACE_URL" \
  -H "Content-Type: application/json" \
  -d "$LISTING_JSON" | jq
