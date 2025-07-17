#!/bin/bash

# Deployment script for Pinecone RAG migration

set -e

echo "🚀 Deploying Marktplaats Backend with Pinecone RAG"
echo "=================================================="

# Check required environment variables
if [ -z "$MARKTPLAATS_CLIENT_ID" ]; then
    echo "❌ Error: MARKTPLAATS_CLIENT_ID not set"
    exit 1
fi

if [ -z "$MARKTPLAATS_CLIENT_SECRET" ]; then
    echo "❌ Error: MARKTPLAATS_CLIENT_SECRET not set"
    exit 1
fi

if [ -z "$PINECONE_API_KEY" ]; then
    echo "❌ Error: PINECONE_API_KEY not set"
    echo "   Please set: export PINECONE_API_KEY='your_api_key'"
    exit 1
fi

echo "✅ Environment variables validated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Validate Pinecone connection
echo "🔍 Validating Pinecone connection..."
python -c "
import os
from pinecone import Pinecone
try:
    pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
    indexes = pc.list_indexes()
    index_names = [idx.name for idx in indexes]
    if 'marktplaats-taxonomy' in index_names:
        print('✅ Pinecone index found: marktplaats-taxonomy')
    else:
        print('❌ Pinecone index not found: marktplaats-taxonomy')
        print('   Available indexes:', index_names)
        exit(1)
except Exception as e:
    print(f'❌ Pinecone connection failed: {e}')
    exit(1)
"

# Deploy with Serverless Framework
echo "🚢 Deploying with Serverless Framework..."
serverless deploy --verbose

echo "✅ Deployment completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Test the deployed endpoint"
echo "2. Monitor CloudWatch logs"
echo "3. Validate cost reduction"
echo ""
echo "💰 Expected savings: ~\$100+/month (OpenSearch → Pinecone free tier)"