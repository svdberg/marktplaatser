#!/bin/bash

set -e

# Read endpoints from file
GENERATE_ENDPOINT=$(sed -n '1p' endpoint.txt)
CREATE_ENDPOINT=$(sed -n '2p' endpoint.txt)

IMAGE_FILE=${1:-sample.jpg}

if [ -z "$GENERATE_ENDPOINT" ] || [ -z "$CREATE_ENDPOINT" ]; then
  echo "Could not read endpoints from endpoint.txt"
  exit 1
fi

if [ ! -f "$IMAGE_FILE" ]; then
  echo "Image file '$IMAGE_FILE' not found."
  exit 1
fi

BASE64_IMAGE=$(base64 -i "$IMAGE_FILE" | tr -d '\n')

echo "=== Step 1: Generating listing data ==="
echo "Using endpoint: $GENERATE_ENDPOINT"

LISTING_RESPONSE=$(curl -s -X POST "$GENERATE_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"${BASE64_IMAGE}\"}")

echo "Listing generation response:"
echo "$LISTING_RESPONSE" | jq .

# Check if listing generation was successful
if echo "$LISTING_RESPONSE" | jq -e '.error' > /dev/null; then
  echo "❌ Listing generation failed"
  exit 1
fi

echo "✅ Listing generated successfully"

echo ""
echo "=== Step 2: Creating advertisement ==="
echo "Using endpoint: $CREATE_ENDPOINT"

# Extract listing data for the create advertisement call
LISTING_DATA=$(echo "$LISTING_RESPONSE" | jq '{
  title: .title,
  description: .description,
  categoryId: .categoryId,
  attributes: .attributes
}')

# Prepare the complete request for creating advertisement
CREATE_REQUEST=$(jq -n \
  --argjson listingData "$LISTING_DATA" \
  --arg image "$BASE64_IMAGE" \
  '{
    listingData: $listingData,
    image: $image,
    userDetails: {
      postcode: "1234AB",
      priceModel: {
        modelType: "fixed",
        askingPrice: 50
      }
    }
  }')

echo "Creating advertisement..."

CREATE_RESPONSE=$(curl -s -X POST "$CREATE_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$CREATE_REQUEST")

echo "Advertisement creation response:"
echo "$CREATE_RESPONSE" | jq .

# Check if advertisement creation was successful
if echo "$CREATE_RESPONSE" | jq -e '.error' > /dev/null; then
  echo "❌ Advertisement creation failed"
  exit 1
fi

echo "✅ Advertisement created successfully!"

# Extract and display key information
ADVERTISEMENT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.advertisementId // empty')
IMAGE_URL=$(echo "$CREATE_RESPONSE" | jq -r '.imageUrl // empty')

if [ -n "$ADVERTISEMENT_ID" ]; then
  echo "📝 Advertisement ID: $ADVERTISEMENT_ID"
fi

if [ -n "$IMAGE_URL" ]; then
  echo "🖼️  Image URL: $IMAGE_URL"
fi

echo ""
echo "🎉 Complete workflow test successful!"