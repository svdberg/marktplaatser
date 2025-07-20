#!/usr/bin/env python3
"""
Setup script for Pinecone vector database to replace AWS OpenSearch.
"""

import os
import json
import boto3
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any

# Configuration
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT', 'us-east-1')
INDEX_NAME = "marktplaats-taxonomy"
EMBEDDING_DIMENSION = 1024  # AWS Titan Text Embeddings v2 default dimension

def create_pinecone_index():
    """Create Pinecone index for taxonomy vectors."""
    
    print("🚀 Setting up Pinecone for Marktplaats taxonomy...")
    
    if not PINECONE_API_KEY:
        print("❌ Error: PINECONE_API_KEY environment variable not set")
        print("   Please set your Pinecone API key:")
        print("   export PINECONE_API_KEY='your_api_key_here'")
        return False
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # List existing indexes
        existing_indexes = pc.list_indexes()
        print(f"📋 Existing indexes: {[idx.name for idx in existing_indexes]}")
        
        # Delete existing index if it exists
        if INDEX_NAME in [idx.name for idx in existing_indexes]:
            print(f"🗑️  Deleting existing index: {INDEX_NAME}")
            pc.delete_index(INDEX_NAME)
        
        # Create new index
        print(f"🔧 Creating new index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region=PINECONE_ENVIRONMENT
            )
        )
        
        print(f"✅ Successfully created Pinecone index: {INDEX_NAME}")
        print(f"   - Dimension: {EMBEDDING_DIMENSION}")
        print(f"   - Metric: cosine")
        print(f"   - Cloud: aws")
        print(f"   - Region: {PINECONE_ENVIRONMENT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Pinecone: {e}")
        return False

def get_embedding(text: str) -> List[float]:
    """Generate embedding using AWS Titan Text Embeddings v2."""
    
    session = boto3.Session(region_name="eu-west-1")
    bedrock_runtime = session.client("bedrock-runtime")
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({
                "inputText": text,
                "normalize": True
            }),
            contentType="application/json",
            accept="application/json"
        )
        
        result = json.loads(response["body"].read().decode("utf-8"))
        return result["embedding"]
        
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return []

def test_pinecone_connection():
    """Test Pinecone connection and basic operations."""
    
    print("\n🔍 Testing Pinecone connection...")
    
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Connect to index
        index = pc.Index(INDEX_NAME)
        
        # Test embedding generation
        test_text = "kitesurfboard Flysurfer Radical watersport"
        embedding = get_embedding(test_text)
        
        if not embedding:
            print("❌ Failed to generate embedding")
            return False
            
        # Test upsert
        test_vector = {
            "id": "test-1",
            "values": embedding,
            "metadata": {
                "categoryId": 1404,
                "categoryName": "Kitesurfen",
                "text": test_text,
                "keywords": ["kitesurfboard", "watersport", "flysurfer"]
            }
        }
        
        index.upsert(vectors=[test_vector])
        print("✅ Test vector upserted successfully")
        
        # Wait for index to be ready
        print("⏳ Waiting for index to be ready...")
        time.sleep(5)
        
        # Test query
        query_results = index.query(
            vector=embedding,
            top_k=1,
            include_metadata=True
        )
        
        if query_results.matches:
            match = query_results.matches[0]
            print(f"✅ Test query successful:")
            print(f"   - Score: {match.score:.4f}")
            print(f"   - Category: {match.metadata.get('categoryName')}")
            print(f"   - ID: {match.metadata.get('categoryId')}")
        else:
            print("❌ Test query returned no results")
            return False
            
        # Clean up test vector
        index.delete(ids=["test-1"])
        print("✅ Test vector cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Pinecone: {e}")
        return False

def main():
    """Main setup function."""
    
    print("🔧 Pinecone Setup for Marktplaats RAG Migration")
    print("=" * 50)
    
    # Step 1: Create index
    if not create_pinecone_index():
        return
    
    # Step 2: Test connection
    if not test_pinecone_connection():
        return
    
    print("\n🎯 Next Steps:")
    print("1. Run upload_to_pinecone.py to populate the index")
    print("2. Update bedrock_rag_utils.py to use Pinecone")
    print("3. Test the new RAG implementation")
    print("4. Deploy and validate cost reduction")

if __name__ == "__main__":
    main()