#!/bin/bash

# Configuration
IMAGE="sample.jpg"
ENCODED="image.txt"
PAYLOAD="payload.json"
# Get endpoint from deploy script output
if [ -f "endpoint.txt" ]; then
  ENDPOINT=$(cat endpoint.txt)
else
  echo "❌ Error: endpoint.txt not found. Run deploy.sh first."
  exit 1
fi

# Check if image file exists
if [ ! -f "$IMAGE" ]; then
  echo "❌ Error: Image file '$IMAGE' not found."
  exit 1
fi

# Encode image to base64 using macOS-compatible syntax
echo "📦 Encoding image..."
base64 -i "$IMAGE" -o "$ENCODED"

# Create JSON payload
echo "📝 Creating payload..."
cat <<EOF > "$PAYLOAD"
{
  "image_base64": "$(cat $ENCODED)"
}
EOF

# Send the request
echo "🚀 Sending request to Lambda..."
curl -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d @"$PAYLOAD"

echo -e "\n✅ Done."
