#!/usr/bin/env python3
"""
Upload taxonomy documents to Pinecone vector database.
"""

import os
import json
import boto3
import glob
from pinecone import Pinecone
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configuration
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
INDEX_NAME = "marktplaats-taxonomy-v2"  # Enhanced with attribute data
EMBEDDING_DIMENSION = 1024
BATCH_SIZE = 100  # Pinecone batch size limit
MAX_WORKERS = 5   # Concurrent embedding generation

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
        print(f"❌ Error generating embedding for text: {text[:50]}... - {e}")
        return []

def load_taxonomy_documents() -> List[Dict[str, Any]]:
    """Load taxonomy documents from kb_documents directory."""
    
    documents = []
    kb_dir = "kb_documents"
    
    if not os.path.exists(kb_dir):
        print(f"❌ Error: {kb_dir} directory not found")
        return documents
    
    json_files = glob.glob(f"{kb_dir}/*.json")
    print(f"📁 Found {len(json_files)} taxonomy documents")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
    
    return documents

def prepare_vector_data(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare documents for Pinecone upload."""
    
    print("🔄 Preparing vector data...")
    
    vectors = []
    
    for doc in documents:
        try:
            category_id = doc.get('categoryId')
            category_name = doc.get('categoryName', 'Unknown')
            category_path = doc.get('categoryPath', '')
            keywords = doc.get('keywords', [])
            description = doc.get('description', '')
            
            # Skip documents with invalid category IDs
            if category_id is None or category_id == 0:
                print(f"⚠️  Skipping document with invalid categoryId: {category_id}")
                continue
            
            # Ensure all metadata values are valid for Pinecone
            clean_keywords = [str(k) for k in keywords if k is not None] if keywords else []
            clean_description = str(description) if description else ""
            clean_category_name = str(category_name) if category_name else "Unknown"
            clean_category_path = str(category_path) if category_path else ""
            
            # Process attributes for storage (compact format for Pinecone 40KB limit)
            attributes_info = []
            attributes_compact = {}  # More compact format
            
            if doc.get('attributes'):
                for attr in doc['attributes']:
                    key = attr.get('key', '')
                    # Store compact attribute info
                    attributes_compact[key] = {
                        'label': attr.get('label', ''),
                        'type': attr.get('type', 'STRING'),
                        'mandatory': attr.get('mandatory', False),
                        'values': attr.get('predefinedValues', [])[:10],  # Limit to first 10 values
                        'group': attr.get('group', '')
                    }
                    
                    # Keep full format for searchable text
                    attr_info = {
                        'key': key,
                        'label': attr.get('label', ''),
                        'type': attr.get('type', 'STRING'),
                        'mandatory': attr.get('mandatory', False),
                        'searchable': attr.get('searchable', False),
                        'group': attr.get('group', ''),
                        'predefinedValues': attr.get('predefinedValues', []),
                        'maxLength': attr.get('maxLength', '')
                    }
                    attributes_info.append(attr_info)
            
            # Create searchable text combining all relevant fields INCLUDING attributes
            searchable_text = f"{clean_category_name} {clean_category_path} {clean_description}"
            if clean_keywords:
                searchable_text += f" {' '.join(clean_keywords)}"
            
            # Add attribute information to searchable text
            if attributes_info:
                attr_text = []
                for attr in attributes_info:
                    attr_text.append(f"{attr['label']} ({attr['key']})")
                    if attr['predefinedValues']:
                        attr_text.extend(attr['predefinedValues'][:5])  # First 5 values
                searchable_text += f" {' '.join(attr_text)}"
            
            # Convert attributes to JSON string for Pinecone storage
            attributes_json = json.dumps(attributes_compact) if attributes_compact else ""
            
            vector_data = {
                'id': f"category_{category_id}",
                'text': searchable_text,
                'metadata': {
                    'categoryId': int(category_id),  # Ensure it's an integer
                    'categoryName': clean_category_name,
                    'categoryPath': clean_category_path,
                    'keywords': clean_keywords,
                    'description': clean_description,
                    'level': int(doc.get('level', 2)),
                    'supportsAttributes': bool(doc.get('supportsAttributes', False)),
                    'attributeCount': int(doc.get('attributeCount', 0)),
                    'attributes': attributes_json  # Store attributes as JSON string
                }
            }
            
            vectors.append(vector_data)
            
        except Exception as e:
            print(f"❌ Error preparing vector for doc {doc.get('categoryId', 'unknown')}: {e}")
    
    print(f"✅ Prepared {len(vectors)} vectors for upload")
    return vectors

def generate_embeddings_batch(vectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate embeddings for a batch of vectors using threading."""
    
    print(f"🔄 Generating embeddings for {len(vectors)} vectors...")
    
    def generate_single_embedding(vector_data):
        embedding = get_embedding(vector_data['text'])
        if embedding:
            return {
                'id': vector_data['id'],
                'values': embedding,
                'metadata': vector_data['metadata']
            }
        return None
    
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_vector = {
            executor.submit(generate_single_embedding, vector): vector 
            for vector in vectors
        }
        
        # Collect results
        for future in as_completed(future_to_vector):
            result = future.result()
            if result:
                results.append(result)
            
            # Progress indicator
            if len(results) % 10 == 0:
                print(f"   Generated {len(results)}/{len(vectors)} embeddings...")
    
    print(f"✅ Generated {len(results)} embeddings successfully")
    return results

def upload_to_pinecone(vectors: List[Dict[str, Any]]) -> bool:
    """Upload vectors to Pinecone index."""
    
    print(f"📤 Uploading {len(vectors)} vectors to Pinecone...")
    
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        
        # Upload in batches
        for i in range(0, len(vectors), BATCH_SIZE):
            batch = vectors[i:i + BATCH_SIZE]
            
            print(f"   Uploading batch {i//BATCH_SIZE + 1}/{(len(vectors) + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} vectors)...")
            
            index.upsert(vectors=batch)
            
            # Rate limiting - Pinecone free tier has limits
            time.sleep(1)
        
        print("✅ All vectors uploaded successfully")
        
        # Verify upload
        stats = index.describe_index_stats()
        print(f"📊 Index stats: {stats.total_vector_count} vectors, {stats.dimension} dimensions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to Pinecone: {e}")
        return False

def test_search(query_text: str = "kitesurfboard watersport"):
    """Test search functionality."""
    
    print(f"\n🔍 Testing search with query: '{query_text}'")
    
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        
        # Generate query embedding
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            print("❌ Failed to generate query embedding")
            return
        
        # Search
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
        
        print(f"📋 Top {len(results.matches)} results:")
        for i, match in enumerate(results.matches, 1):
            metadata = match.metadata
            print(f"   {i}. {metadata.get('categoryName')} (ID: {metadata.get('categoryId')})")
            print(f"      Score: {match.score:.4f}")
            print(f"      Path: {metadata.get('categoryPath', 'N/A')}")
            print()
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")

def main():
    """Main upload function."""
    
    print("📤 Uploading Taxonomy to Pinecone")
    print("=" * 40)
    
    if not PINECONE_API_KEY:
        print("❌ Error: PINECONE_API_KEY environment variable not set")
        return
    
    # Step 1: Load taxonomy documents
    documents = load_taxonomy_documents()
    if not documents:
        print("❌ No documents to upload")
        return
    
    # Step 2: Prepare vector data
    vectors = prepare_vector_data(documents)
    if not vectors:
        print("❌ No vectors prepared")
        return
    
    # Step 3: Generate embeddings
    embedded_vectors = generate_embeddings_batch(vectors)
    if not embedded_vectors:
        print("❌ No embeddings generated")
        return
    
    # Step 4: Upload to Pinecone
    if not upload_to_pinecone(embedded_vectors):
        print("❌ Upload failed")
        return
    
    # Step 5: Test search
    test_search("kitesurfboard watersport")
    test_search("schommelstoel meubel hout")
    
    print("\n🎯 Upload completed successfully!")
    print("   Next: Update bedrock_rag_utils.py to use Pinecone")

if __name__ == "__main__":
    main()