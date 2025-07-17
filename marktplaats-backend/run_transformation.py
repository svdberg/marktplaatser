#!/usr/bin/env python3
"""
Simple runner script to test the taxonomy transformation.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now import and run the transformer
try:
    from marktplaats_backend.taxonomy_transformer import TaxonomyTransformer
    
    print("🚀 Running taxonomy transformation...")
    print("=" * 60)
    
    # Path to taxonomy file
    taxonomy_path = "/Users/sander.vandenberg/src/marktplaatser/taxonomy-mpnl.json"
    
    # Create transformer
    transformer = TaxonomyTransformer(taxonomy_path)
    
    # Run transformation (but limit to first 10 categories for testing)
    print("📋 Loading and analyzing taxonomy structure...")
    taxonomy_data = transformer.load_taxonomy()
    
    print(f"🔍 Analyzing JSON structure...")
    if '_embedded' in taxonomy_data and 'mp:category' in taxonomy_data['_embedded']:
        root_categories = taxonomy_data['_embedded']['mp:category']
        print(f"📊 Found {len(root_categories)} root categories")
        
        # Show first few categories
        for i, cat in enumerate(root_categories[:3]):
            print(f"  {i+1}. {cat.get('name', 'Unknown')} (ID: {cat.get('categoryId', 'N/A')})")
            
        # Extract level 2 categories
        level_2_cats = transformer.extract_level_2_categories(taxonomy_data)
        print(f"📈 Found {len(level_2_cats)} level 2 categories")
        
        # Show examples of level 2 categories
        print(f"\n📂 Sample level 2 categories:")
        for i, cat in enumerate(level_2_cats[:5]):
            print(f"  {i+1}. {cat['path']} (ID: {cat['categoryId']})")
            
        # Test document creation for first category
        if level_2_cats:
            print(f"\n🔬 Testing document creation...")
            sample_doc = transformer.create_knowledge_base_document(level_2_cats[0])
            
            print(f"📄 Sample document structure:")
            print(f"  Category ID: {sample_doc['categoryId']}")
            print(f"  Name: {sample_doc['categoryName']}")
            print(f"  Path: {sample_doc['categoryPath']}")
            print(f"  Keywords: {sample_doc['keywords'][:5]}...")  # First 5 keywords
            print(f"  Description length: {len(sample_doc['description'])} chars")
            
            print(f"\n📋 Full sample document:")
            print("-" * 40)
            print(sample_doc['content'])
            print("-" * 40)
            
        print(f"\n✅ Analysis complete!")
        print(f"💡 Ready to generate {len(level_2_cats)} Knowledge Base documents")
        
    else:
        print("❌ Unexpected taxonomy structure")
        print(f"Available keys: {list(taxonomy_data.keys())}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Next steps:")
print("1. Run full transformation to generate all documents")
print("2. Create S3 bucket for Knowledge Base")
print("3. Set up Bedrock Knowledge Base")
print("4. Update Lambda functions to use RAG")