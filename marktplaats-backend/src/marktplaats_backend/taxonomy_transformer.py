#!/usr/bin/env python3
"""
Transform taxonomy-mpnl.json into Bedrock Knowledge Base documents.

This script extracts level 2 categories (those that support attributes)
and creates rich documents for semantic search.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid


class TaxonomyTransformer:
    """Transform Marktplaats taxonomy into Knowledge Base documents."""
    
    def __init__(self, taxonomy_path: str):
        """Initialize with path to taxonomy JSON file."""
        self.taxonomy_path = Path(taxonomy_path)
        self.level_2_categories = []
        
    def load_taxonomy(self) -> Dict[str, Any]:
        """Load and parse the taxonomy JSON file."""
        print(f"📁 Loading taxonomy from: {self.taxonomy_path}")
        
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {self.taxonomy_path}")
            
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"✅ Loaded taxonomy file ({self.taxonomy_path.stat().st_size / (1024*1024):.1f} MB)")
        return data
        
    def extract_level_2_categories(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all level 2 categories that support attributes."""
        
        # Handle both API response format and taxonomy file format
        if isinstance(data, dict) and '_embedded' in data and 'mp:category' in data['_embedded']:
            # API response format
            categories = data['_embedded']['mp:category']
        elif isinstance(data, dict) and 'children' in data:
            # Taxonomy file format with nested children - extract level 2 categories
            level_2_cats = []
            
            # Level 1: data.children (main categories)
            for level1_cat in data.get('children', []):
                level1_id = level1_cat.get('id')
                level1_name = level1_cat.get('label', {}).get('nl_NL', 'Unknown')
                
                # Level 2: level1_cat.children (subcategories with attributes)
                for level2_cat in level1_cat.get('children', []):
                    if 'attributeGroups' in level2_cat and level2_cat.get('attributeGroups'):
                        cat_id = level2_cat.get('id')
                        cat_name = level2_cat.get('label', {}).get('nl_NL', 'Unknown')
                        path = f"{level1_name} > {cat_name}"
                        
                        # Extract attribute schemas
                        attribute_groups = level2_cat.get('attributeGroups', [])
                        attributes_list = self.extract_attribute_schemas(attribute_groups)
                        
                        level_2_cats.append({
                            'categoryId': cat_id,
                            'name': cat_name,
                            'path': path,
                            'parentId': level1_id,
                            'parentPath': level1_name,
                            'labels': level2_cat.get('label', {}),
                            'level': 2,
                            'attributeGroups': attribute_groups,
                            'attributes': attributes_list,
                            'raw_category': level2_cat  # Keep original for reference
                        })
            
            print(f"📊 Extracted {len(level_2_cats)} level 2 categories from nested format")
            return level_2_cats
        elif isinstance(data, list):
            # Flat list format - assume these are level 2 categories with attributes
            level_2_cats = []
            for cat in data:
                if 'attributeGroups' in cat and cat.get('attributeGroups'):
                    # This is a level 2 category with attributes
                    cat_id = cat.get('id')
                    cat_name = cat.get('label', {}).get('nl_NL', 'Unknown')
                    
                    level_2_cats.append({
                        'categoryId': cat_id,
                        'name': cat_name,
                        'path': cat_name,  # No parent path available in flat format
                        'parentId': None,
                        'parentPath': '',
                        'labels': cat.get('label', {}),
                        'level': 2,
                        'raw_category': cat  # Keep original for reference
                    })
            
            print(f"📊 Extracted {len(level_2_cats)} level 2 categories from flat format")
            return level_2_cats
        else:
            raise ValueError("Invalid taxonomy structure - unknown format")
            
        # Handle nested format (original logic)
        level_2_cats = []
        
        def extract_recursive(cats: List[Dict], level: int = 1, parent_path: str = "", parent_id: Optional[int] = None):
            """Recursively extract categories at level 2."""
            for cat in cats:
                cat_id = cat.get('categoryId')
                cat_name = cat.get('name', 'Unknown')
                current_path = f"{parent_path} > {cat_name}" if parent_path else cat_name
                
                # Level 2 categories are what we want (they support attributes)
                if level == 2:
                    level_2_cats.append({
                        'categoryId': cat_id,
                        'name': cat_name,
                        'path': current_path,
                        'parentId': parent_id,
                        'parentPath': parent_path,
                        'labels': cat.get('labels', {}),
                        'level': level,
                        'raw_category': cat  # Keep original for reference
                    })
                
                # Continue recursion for subcategories
                if '_embedded' in cat and 'mp:category' in cat['_embedded']:
                    subcategories = cat['_embedded']['mp:category']
                    extract_recursive(subcategories, level + 1, current_path, cat_id)
        
        extract_recursive(categories)
        
        print(f"📊 Extracted {len(level_2_cats)} level 2 categories")
        return level_2_cats
        
    def extract_attribute_schemas(self, attribute_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and process attribute schemas from attribute groups."""
        
        attributes_list = []
        
        for group in attribute_groups:
            group_label = group.get('label', {}).get('nl_NL', 'Unknown Group')
            group_attributes = group.get('attributes', [])
            
            for attr in group_attributes:
                attr_schema = {
                    'key': attr.get('key', ''),
                    'label': attr.get('label', {}).get('nl_NL', ''),
                    'type': attr.get('type', 'STRING'),
                    'mandatory': attr.get('mandatory', False),
                    'searchable': attr.get('searchable', False),
                    'group': group_label
                }
                
                # Add type-specific properties
                if attr_schema['type'] == 'STRING':
                    if 'length' in attr:
                        attr_schema['maxLength'] = attr['length']
                    if 'values' in attr and 'nl_NL' in attr['values']:
                        attr_schema['predefinedValues'] = attr['values']['nl_NL']
                        
                elif attr_schema['type'] == 'NUMBER':
                    if 'range' in attr:
                        attr_schema['range'] = attr['range']
                    if 'precision' in attr:
                        attr_schema['precision'] = attr['precision']
                    if 'postfix' in attr and 'nl_NL' in attr['postfix']:
                        attr_schema['unit'] = attr['postfix']['nl_NL']
                        
                elif attr_schema['type'] == 'LIST':
                    if 'values' in attr and 'nl_NL' in attr['values']:
                        attr_schema['options'] = attr['values']['nl_NL']
                
                attributes_list.append(attr_schema)
        
        return attributes_list
        
    def generate_category_keywords(self, category: Dict[str, Any]) -> List[str]:
        """Generate relevant keywords for a category based on its name and path."""
        
        name = category['name'].lower()
        path = category['path'].lower()
        
        # Base keywords from category name and path
        keywords = []
        
        # Split name and path into words
        name_words = name.replace('-', ' ').replace('&', 'and').split()
        path_words = path.replace('-', ' ').replace('&', 'and').replace('>', ' ').split()
        
        keywords.extend(name_words)
        keywords.extend(path_words)
        
        # Add specific domain keywords based on category patterns
        keyword_mappings = {
            'auto': ['car', 'vehicle', 'automotive', 'motor'],
            'telefoon': ['phone', 'mobile', 'smartphone', 'cellular'],
            'computer': ['pc', 'laptop', 'desktop', 'computing'],
            'fiets': ['bicycle', 'bike', 'cycling'],
            'kleding': ['clothing', 'apparel', 'fashion', 'wear'],
            'huis': ['house', 'home', 'housing', 'property'],
            'tuin': ['garden', 'outdoor', 'yard'],
            'boek': ['book', 'literature', 'reading'],
            'muziek': ['music', 'audio', 'sound'],
            'sport': ['sports', 'fitness', 'exercise'],
            'kind': ['child', 'kids', 'baby', 'children'],
            'dier': ['animal', 'pet', 'pets'],
            'verzameling': ['collection', 'collectible', 'antique'],
            'zakelijk': ['business', 'professional', 'commercial'],
        }
        
        # Add relevant keywords based on category content
        for dutch_term, english_terms in keyword_mappings.items():
            if dutch_term in name or dutch_term in path:
                keywords.extend(english_terms)
        
        # Remove duplicates and empty strings
        keywords = list(set([k.strip() for k in keywords if k.strip()]))
        
        return keywords
        
    def create_category_description(self, category: Dict[str, Any]) -> str:
        """Create a rich description for a category for better semantic search."""
        
        name = category['name']
        path = category['path']
        keywords = self.generate_category_keywords(category)
        
        # Base description
        description = f"This category is for {name} items"
        
        if category['parentPath']:
            description += f" under {category['parentPath']}"
            
        description += f". Full category path: {path}."
        
        # Add context based on category type
        if 'auto' in name.lower() or 'car' in keywords:
            description += " This includes automotive parts, accessories, and vehicle-related items."
        elif 'telefoon' in name.lower() or 'phone' in keywords:
            description += " This includes mobile phones, smartphones, and phone accessories."
        elif 'computer' in name.lower() or 'laptop' in keywords:
            description += " This includes computers, laptops, and IT equipment."
        elif 'kleding' in name.lower() or 'clothing' in keywords:
            description += " This includes clothing, apparel, and fashion items."
        elif 'huis' in name.lower() or 'home' in keywords:
            description += " This includes home improvement, household items, and living essentials."
        elif 'sport' in name.lower() or 'fitness' in keywords:
            description += " This includes sports equipment, fitness gear, and athletic items."
        elif 'kind' in name.lower() or 'baby' in keywords:
            description += " This includes children's items, baby products, and kids' accessories."
        
        # Add keyword context
        if keywords:
            relevant_keywords = [k for k in keywords if len(k) > 2][:10]  # Top 10 meaningful keywords
            description += f" Related terms: {', '.join(relevant_keywords)}."
            
        return description
        
    def create_knowledge_base_document(self, category: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document suitable for Bedrock Knowledge Base."""
        
        keywords = self.generate_category_keywords(category)
        description = self.create_category_description(category)
        
        # Get attributes and create detailed attribute descriptions
        attributes = category.get('attributes', [])
        attribute_groups = category.get('attributeGroups', [])
        
        # Create detailed attribute description for the content
        attribute_descriptions = []
        if attributes:
            attribute_descriptions.append(f"\nAvailable Attributes ({len(attributes)} total):")
            for attr in attributes:
                attr_desc = f"- {attr['label']} ({attr['key']}): {attr['type']}"
                if attr.get('mandatory'):
                    attr_desc += " [REQUIRED]"
                if attr.get('predefinedValues'):
                    options = attr['predefinedValues'][:5]  # First 5 options
                    attr_desc += f" Options: {', '.join(options)}"
                    if len(attr['predefinedValues']) > 5:
                        attr_desc += f" (+{len(attr['predefinedValues'])-5} more)"
                elif attr.get('options'):
                    options = attr['options'][:5]  # First 5 options
                    attr_desc += f" Options: {', '.join(options)}"
                    if len(attr['options']) > 5:
                        attr_desc += f" (+{len(attr['options'])-5} more)"
                elif attr.get('range'):
                    attr_desc += f" Range: {attr['range']}"
                    if attr.get('unit'):
                        attr_desc += f" {attr['unit']}"
                attribute_descriptions.append(attr_desc)

        # Create the document structure
        document = {
            'categoryId': category['categoryId'],
            'categoryName': category['name'],
            'categoryPath': category['path'],
            'parentCategory': category['parentPath'],
            'level': category['level'],
            'description': description,
            'keywords': keywords,
            'dutchLabels': category['labels'],
            'attributes': attributes,  # Include full attribute schemas
            'attributeGroups': attribute_groups,  # Include raw attribute groups
            'attributeCount': len(attributes),
            'supportsAttributes': True,  # Level 2 categories support attributes
            'documentId': f"category_{category['categoryId']}",
            'content': f"""
Category: {category['name']}
Path: {category['path']}
Description: {description}
Keywords: {', '.join(keywords)}
Category ID: {category['categoryId']}
Supports Attributes: Yes (Level 2 Category)
Attribute Count: {len(attributes)}
{''.join(attribute_descriptions)}
            """.strip()
        }
        
        return document
        
    def transform_all_categories(self) -> List[Dict[str, Any]]:
        """Transform all level 2 categories into Knowledge Base documents."""
        
        print("🚀 Starting taxonomy transformation...")
        
        # Load taxonomy
        taxonomy_data = self.load_taxonomy()
        
        # Extract level 2 categories with full attribute schemas
        level_2_categories = self.extract_level_2_categories(taxonomy_data)
        
        # Transform to documents
        documents = []
        for i, category in enumerate(level_2_categories, 1):
            try:
                doc = self.create_knowledge_base_document(category)
                documents.append(doc)
                
                if i % 50 == 0:  # Progress update every 50 categories
                    print(f"📄 Processed {i}/{len(level_2_categories)} categories...")
                    
            except Exception as e:
                print(f"❌ Error processing category {category.get('name', 'Unknown')}: {e}")
                continue
                
        print(f"✅ Transformed {len(documents)} categories into Knowledge Base documents")
        return documents
        
    def save_documents(self, documents: List[Dict[str, Any]], output_dir: str = "kb_documents"):
        """Save documents as individual JSON files for S3 upload."""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"💾 Saving {len(documents)} documents to {output_path}...")
        
        for doc in documents:
            # Create filename from category name (sanitized)
            category_name = doc['categoryName'].replace('/', '_').replace(' ', '_').replace('&', 'and')
            filename = f"category_{doc['categoryId']}_{category_name}.json"
            
            # Ensure filename is not too long
            if len(filename) > 100:
                filename = f"category_{doc['categoryId']}.json"
                
            file_path = output_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
                
        print(f"✅ Saved documents to {output_path}")
        
        # Create a manifest file
        manifest = {
            'total_documents': len(documents),
            'created_at': str(uuid.uuid4()),
            'source_file': str(self.taxonomy_path),
            'document_structure': list(documents[0].keys()) if documents else [],
            'sample_document': documents[0] if documents else None
        }
        
        with open(output_path / 'manifest.json', 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            
        print(f"📋 Created manifest file: {output_path / 'manifest.json'}")
        return output_path


def main():
    """Main function to run the transformation."""
    
    # Path to the taxonomy file (adjust as needed)
    taxonomy_path = "/Users/sander.vandenberg/src/marktplaatser/taxonomy-mpnl.json"
    
    try:
        transformer = TaxonomyTransformer(taxonomy_path)
        documents = transformer.transform_all_categories()
        
        if documents:
            output_dir = transformer.save_documents(documents)
            print(f"\n🎉 Transformation complete!")
            print(f"📁 Output directory: {output_dir}")
            print(f"📊 Generated {len(documents)} Knowledge Base documents")
            print(f"\nNext steps:")
            print("1. Upload documents to S3 bucket")
            print("2. Create Bedrock Knowledge Base")
            print("3. Configure with Titan embeddings")
            print("4. Update Lambda to use RetrieveAndGenerate API")
        else:
            print("❌ No documents generated")
            
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()