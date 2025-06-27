#!/bin/bash

# Frontend deployment script for AWS S3 + CloudFront

set -e

echo "🚀 Deploying Marktplaats Frontend to AWS..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Generate static files
echo "🏗️  Building static files..."
npm run generate

# Deploy infrastructure and sync files
echo "☁️  Deploying to AWS..."
npx serverless deploy --stage prod

# Sync files to S3
echo "📤 Syncing files to S3..."
npx serverless s3sync --stage prod

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your frontend is now live at:"
echo "   S3 Website: $(npx serverless info --stage prod | grep 'WebsiteURL' | cut -d' ' -f2)"
echo "   CloudFront: $(npx serverless info --stage prod | grep 'CloudFrontURL' | cut -d' ' -f2)"
echo ""
echo "💡 Note: CloudFront distribution may take 10-15 minutes to fully deploy"