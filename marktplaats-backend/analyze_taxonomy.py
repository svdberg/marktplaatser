#!/usr/bin/env python3
"""
Script to analyze the taxonomy-mpnl.json file structure
and prepare it for Bedrock Knowledge Base transformation.
"""

import json
from pathlib import Path

def analyze_taxonomy():
    """Analyze the taxonomy file structure."""
    
    # Path to the taxonomy file
    taxonomy_path = Path(__file__).parent.parent / "taxonomy-mpnl.json"
    
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy file not found at: {taxonomy_path}")
        return
    
    print(f"📁 Analyzing taxonomy file: {taxonomy_path}")
    print(f"📊 File size: {taxonomy_path.stat().st_size / (1024*1024):.1f} MB")
    
    try:
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            # Read first 1000 characters to understand structure
            sample = f.read(1000)
            print(f"\n📄 File sample (first 1000 chars):")
            print("=" * 50)
            print(sample)
            print("=" * 50)
            
            # Reset and load full JSON
            f.seek(0)
            data = json.load(f)
            
        print(f"\n🔍 JSON Structure Analysis:")
        print(f"Root keys: {list(data.keys())}")
        
        # Analyze the structure based on what we expect
        if '_embedded' in data and 'mp:category' in data['_embedded']:
            categories = data['_embedded']['mp:category']
            print(f"📊 Total root categories: {len(categories)}")
            
            # Analyze first few categories
            level_2_count = 0
            total_categories = 0
            
            def count_categories(cats, level=1, parent_path=""):
                nonlocal level_2_count, total_categories
                count = 0
                
                for cat in cats:
                    total_categories += 1
                    cat_name = cat.get('name', 'Unknown')
                    cat_id = cat.get('categoryId', 'Unknown')
                    current_path = f"{parent_path} > {cat_name}" if parent_path else cat_name
                    
                    if level == 2:
                        level_2_count += 1
                        if level_2_count <= 5:  # Show first 5 level 2 categories
                            print(f"  Level 2: {current_path} (ID: {cat_id})")
                    
                    # Recurse into subcategories
                    if '_embedded' in cat and 'mp:category' in cat['_embedded']:
                        sub_cats = cat['_embedded']['mp:category']
                        count += len(sub_cats)
                        count += count_categories(sub_cats, level + 1, current_path)
                
                return count
            
            print(f"\n📂 Category hierarchy analysis:")
            total_subcats = count_categories(categories)
            
            print(f"\n📈 Summary:")
            print(f"  - Root categories: {len(categories)}")
            print(f"  - Level 2 categories: {level_2_count}")
            print(f"  - Total categories: {total_categories}")
            
            # Show structure of first category
            if categories:
                first_cat = categories[0]
                print(f"\n🔬 Sample category structure:")
                print(f"Category ID: {first_cat.get('categoryId')}")
                print(f"Name: {first_cat.get('name')}")
                print(f"Labels: {first_cat.get('labels', {})}")
                print(f"Has subcategories: {'_embedded' in first_cat}")
                
                if '_embedded' in first_cat and 'mp:category' in first_cat['_embedded']:
                    sub_count = len(first_cat['_embedded']['mp:category'])
                    print(f"Subcategory count: {sub_count}")
                    
                    if sub_count > 0:
                        first_sub = first_cat['_embedded']['mp:category'][0]
                        print(f"First subcategory: {first_sub.get('name')} (ID: {first_sub.get('categoryId')})")
        
        else:
            print("❌ Unexpected JSON structure - no _embedded.mp:category found")
            print(f"Available keys: {list(data.keys())}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")

# Run analysis immediately
print("🚀 Starting taxonomy analysis...")
analyze_taxonomy()
print("✅ Analysis complete!")