#!/usr/bin/env python3
"""
Generate the complete set of Knowledge Base documents from taxonomy.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from marktplaats_backend.taxonomy_transformer import TaxonomyTransformer

def main():
    """Generate all Knowledge Base documents."""
    
    print("🚀 Starting FULL taxonomy transformation for Knowledge Base...")
    print("=" * 70)
    
    # Path to taxonomy file
    taxonomy_path = "/Users/sander.vandenberg/src/marktplaatser/taxonomy-mpnl.json"
    
    try:
        # Create transformer
        transformer = TaxonomyTransformer(taxonomy_path)
        
        # Run full transformation
        print("📊 Processing all level 2 categories...")
        documents = transformer.transform_all_categories()
        
        if documents:
            # Save documents
            output_dir = transformer.save_documents(documents, "kb_documents")
            
            print("\n" + "=" * 70)
            print("🎉 TRANSFORMATION COMPLETE!")
            print("=" * 70)
            print(f"📁 Output directory: {output_dir}")
            print(f"📊 Total documents: {len(documents)}")
            print(f"💾 Files created: {len(documents) + 1} (includes manifest.json)")
            
            # Show some statistics
            print(f"\n📈 Document Statistics:")
            total_keywords = sum(len(doc.get('keywords', [])) for doc in documents)
            avg_keywords = total_keywords / len(documents) if documents else 0
            print(f"  • Average keywords per document: {avg_keywords:.1f}")
            
            # Show sample file names
            output_path = Path(output_dir)
            sample_files = list(output_path.glob("*.json"))[:5]
            print(f"\n📄 Sample files created:")
            for i, file_path in enumerate(sample_files, 1):
                print(f"  {i}. {file_path.name}")
            
            print(f"\n🎯 Next Steps:")
            print(f"1. Create S3 bucket for Knowledge Base")
            print(f"2. Upload documents from {output_dir}/ to S3")
            print(f"3. Create Bedrock Knowledge Base")
            print(f"4. Configure with Titan embeddings")
            print(f"5. Update Lambda functions")
            
            # Show AWS CLI command for next step
            print(f"\n💡 Ready for S3 upload command:")
            print(f"aws s3 cp {output_dir}/ s3://YOUR-BUCKET-NAME/taxonomy/ --recursive")
            
        else:
            print("❌ No documents generated")
            
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()