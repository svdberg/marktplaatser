#!/usr/bin/env python3
"""
Direct test of the clean 3-step RAG implementation without Lambda overhead.
"""

import os
import sys
import base64
import time
from src.marktplaats_backend.bedrock_rag_utils import generate_listing_with_knowledge_base

def test_rag_with_image(image_path: str):
    """Test RAG directly with an image file."""
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"🧪 Testing clean 3-step RAG with: {image_path}")
    print(f"📸 Image size: {len(image_data)} bytes")
    
    # Test with minimal Rekognition data (simulating poor quality labels)
    poor_labels = ['Object', 'Product', 'Outdoors']  # Generic, unhelpful labels
    rekognition_text = []  # No text detected
    
    # Knowledge Base ID from serverless.yaml
    knowledge_base_id = "PORZ8IEECD"
    
    try:
        # Test the clean 3-step RAG approach with timing
        start_time = time.time()
        result = generate_listing_with_knowledge_base(
            image_data=image_data,
            rekognition_labels=poor_labels,
            rekognition_text=rekognition_text,
            knowledge_base_id=knowledge_base_id
        )
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n✅ RAG Test Results (⏱️  {total_time:.2f}s):")
        print(f"📝 Title: {result.get('title', 'N/A')}")
        print(f"📂 Category: {result.get('category', 'N/A')} (ID: {result.get('categoryId', 'N/A')})")
        print(f"💰 Price: €{result.get('estimatedPrice', 'N/A')}")
        print(f"🎯 Confidence: {result.get('priceConfidence', 'N/A')}")
        
        # Performance assessment
        if total_time > 29:
            print(f"⚠️  TIMEOUT RISK: {total_time:.1f}s exceeds API Gateway 29s limit")
        elif total_time > 20:
            print(f"⚠️  SLOW: {total_time:.1f}s is getting close to timeout")
        else:
            print(f"✅ FAST: {total_time:.1f}s is within safe limits")
        
        if '_rag_metadata' in result:
            metadata = result['_rag_metadata']
            print(f"\n🔍 RAG Metadata:")
            print(f"   Product ID: {metadata.get('product_identified', 'N/A')}")
            print(f"   Category Found: {metadata.get('category_found', 'N/A')}")
            print(f"   Clean Approach: {metadata.get('clean_approach', False)}")
        
        return result
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Set AWS region
    os.environ['AWS_REGION'] = 'eu-west-1'
    
    # Get image path from command line
    if len(sys.argv) != 2:
        print("Usage: python test_rag_direct.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        sys.exit(1)
    
    # Run the test
    result = test_rag_with_image(image_path)
    
    if result:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)