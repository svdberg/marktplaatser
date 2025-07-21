"""
Pinecone-based RAG utilities for Marktplaats listing generation.
Replaces AWS Bedrock Knowledge Base with Pinecone vector database.
"""

import os
import json
import boto3
import base64
from typing import List, Dict, Any, Optional
from pinecone import Pinecone

# Configuration
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
INDEX_NAME = "marktplaats-taxonomy-v2"  # Enhanced with attribute data
EMBEDDING_DIMENSION = 1024

# Force region to eu-west-1
os.environ['AWS_REGION'] = 'eu-west-1'


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


def search_categories(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search for relevant categories using Pinecone."""
    
    if not PINECONE_API_KEY:
        print("❌ Error: PINECONE_API_KEY not set")
        return []
    
    try:
        # Generate query embedding
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            return []
        
        # Search Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        categories = []
        for match in results.matches:
            metadata = match.metadata
            # Ensure categoryId is an integer
            category_id = metadata.get('categoryId')
            if category_id is not None:
                category_id = int(category_id)
            
            # Parse attributes JSON if present
            attributes_data = {}
            attributes_json = metadata.get('attributes', '')
            if attributes_json:
                try:
                    attributes_data = json.loads(attributes_json)
                except (json.JSONDecodeError, TypeError):
                    attributes_data = {}
            
            categories.append({
                'categoryId': category_id,
                'categoryName': metadata.get('categoryName'),
                'categoryPath': metadata.get('categoryPath'),
                'score': match.score,
                'keywords': metadata.get('keywords', []),
                'supportsAttributes': metadata.get('supportsAttributes', False),
                'attributes': attributes_data  # Enhanced: include attribute structure
            })
        
        return categories
        
    except Exception as e:
        print(f"❌ Error searching categories: {e}")
        return []


def generate_listing_with_pinecone_rag(images_data: List[bytes] = None,
                                      image_data: bytes = None, 
                                      rekognition_labels: List[str] = None,
                                      rekognition_text: List[str] = None) -> Dict[str, Any]:
    """
    Generate listing using Vision + Pinecone RAG approach.
    1. Claude vision generates main listing (title, description, price)
    2. Pinecone finds relevant categories and attributes
    
    Args:
        images_data: List of image bytes (new multi-image format)
        image_data: Single image bytes (backward compatibility)
        rekognition_labels: List of Rekognition labels
        rekognition_text: List of Rekognition text
    """
    
    # Handle backward compatibility
    if images_data is None and image_data is not None:
        images_data = [image_data]
    elif images_data is None:
        raise ValueError("Either images_data or image_data must be provided")
    
    if rekognition_labels is None:
        rekognition_labels = []
    if rekognition_text is None:
        rekognition_text = []
    
    print("🚀 Starting Vision + Pinecone RAG generation...")
    
    # Create Bedrock client
    session = boto3.Session(region_name="eu-west-1")
    bedrock_runtime = session.client("bedrock-runtime")
    
    # Only use Rekognition text if available
    rekognition_context = ""
    if rekognition_text:
        text_content = ' '.join([text.strip() for text in rekognition_text if len(text.strip()) > 2])
        if text_content:
            rekognition_context = f"\nDetected text: {text_content}"
    
    print(f"🔍 Using Rekognition text: {rekognition_text if rekognition_text else 'None'}")
    
    # Step 1: Claude vision - generate main listing
    print(f"👁️  Step 1: Claude vision for listing generation with {len(images_data)} image(s)...")
    
    # Build vision content with multiple images
    vision_content = []
    
    # Add all images to the request
    for i, img_data in enumerate(images_data):
        image_base64 = base64.b64encode(img_data).decode('utf-8')
        vision_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_base64
            }
        })
    
    # Add the text prompt
    if len(images_data) == 1:
        prompt_text = f"""Maak een Nederlandse Marktplaats advertentie voor dit product:{rekognition_context}

{{
  "title": "[Nederlandse titel max 60 karakters]",
  "description": "[Nederlandse beschrijving 2-3 zinnen]",
  "product_keywords": "[hoofdproduct type merk kleur conditie]",
  "estimatedPrice": [realistische_prijs_euros],
  "priceRange": {{"min": [min_prijs], "max": [max_prijs]}},
  "priceConfidence": "medium"
}}

Geef alleen JSON terug, geen extra tekst."""
    else:
        prompt_text = f"""Maak een Nederlandse Marktplaats advertentie voor dit product gebaseerd op alle {len(images_data)} afbeeldingen:{rekognition_context}

Analyseer alle afbeeldingen samen om een complete beschrijving te maken. Gebruik informatie uit alle foto's voor een betere advertentie.

{{
  "title": "[Nederlandse titel max 60 karakters]",
  "description": "[Nederlandse beschrijving 2-3 zinnen, gebruik details uit alle foto's]",
  "product_keywords": "[hoofdproduct type merk kleur conditie staat details]",
  "estimatedPrice": [realistische_prijs_euros],
  "priceRange": {{"min": [min_prijs], "max": [max_prijs]}},
  "priceConfidence": "medium"
}}

Geef alleen JSON terug, geen extra tekst."""
    
    vision_content.append({
        "type": "text",
        "text": prompt_text
    })

    try:
        # Vision call for main listing
        response = bedrock_runtime.invoke_model(
            modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": vision_content}],
                "max_tokens": 800,
                "temperature": 0.3
            }),
            contentType="application/json",
            accept="application/json"
        )

        body = response["body"].read().decode("utf-8")
        parsed = json.loads(body)
        
        if isinstance(parsed["content"], list):
            vision_text = "".join(part["text"] for part in parsed["content"] if part["type"] == "text").strip()
            
            # Parse JSON from vision response
            try:
                start = vision_text.find('{')
                end = vision_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = vision_text[start:end]
                    vision_listing = json.loads(json_str)
                    print(f"✅ Vision listing generated: {vision_listing.get('title', 'N/A')}")
                else:
                    raise ValueError("No JSON found")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Vision JSON parsing failed: {e}")
                vision_listing = {"product_keywords": "unknown product"}
        else:
            vision_listing = {"product_keywords": "unknown product"}
            
    except Exception as e:
        print(f"❌ Vision failed: {e}")
        vision_listing = {"product_keywords": "unknown product"}
    
    # Step 2: Pinecone search for categories
    print("🔍 Step 2: Pinecone category search...")
    
    product_keywords = vision_listing.get('product_keywords', 'unknown product')
    
    # Search for relevant categories
    categories = search_categories(product_keywords, top_k=3)
    
    if categories:
        best_category = categories[0]  # Highest scoring category
        category_id = best_category['categoryId']
        category_name = best_category['categoryName']
        
        print(f"✅ Found category: {category_name} (ID: {category_id}, score: {best_category['score']:.4f})")
        
        # Step 3: Analyze pricing model suitability
        print("💰 Step 3: Analyzing pricing model suitability...")
        
        # Determine if category is suitable for bidding based on category analysis
        category_name_lower = category_name.lower()
        category_path = best_category.get('categoryPath', '').lower()
        
        # Categories typically suitable for bidding/auctions
        bidding_suitable_keywords = [
            'antiek', 'kunst', 'verzamelen', 'vintage', 'klassiek',
            'zeldzaam', 'uniek', 'limited', 'exclusief', 'collector',
            'handgemaakt', 'design', 'kunstwerk', 'sieraden', 'munten',
            'postzegels', 'boeken', 'platen', 'vinyl', 'memorabilia'
        ]
        
        # Categories typically NOT suitable for bidding
        bidding_unsuitable_keywords = [
            'telefoon', 'computer', 'laptop', 'tablet', 'software',
            'kleding', 'schoenen', 'voeding', 'tickets', 'diensten',
            'verhuur', 'baan', 'stage', 'cursus', 'training'
        ]
        
        # Analyze category for bidding suitability
        bidding_score = 0
        for keyword in bidding_suitable_keywords:
            if keyword in category_name_lower or keyword in category_path:
                bidding_score += 1
        
        for keyword in bidding_unsuitable_keywords:
            if keyword in category_name_lower or keyword in category_path:
                bidding_score -= 2
        
        # Determine suggested pricing model
        if bidding_score > 0:
            suggested_pricing_model = "bidding"
            print(f"✨ Suggested pricing model: bidding (score: {bidding_score})")
        else:
            suggested_pricing_model = "fixed"
            print(f"✨ Suggested pricing model: fixed (score: {bidding_score})")
        
        # Step 4: Generate attributes using retrieved attribute structure
        print("🏷️  Step 4: Generating attributes with retrieved structure...")
        
        # Get attribute structure from Pinecone
        category_attributes = best_category.get('attributes', {})
        
        if category_attributes:
            # Build attribute prompt with actual attribute definitions
            attr_definitions = []
            for key, attr_info in category_attributes.items():
                label = attr_info.get('label', key)
                values = attr_info.get('values', [])
                
                if values:
                    # Use predefined values
                    values_str = f"[{'/'.join(values[:5])}]"  # First 5 values
                    if len(values) > 5:
                        values_str = values_str[:-1] + "/...]"
                else:
                    # No predefined values, generate based on type
                    values_str = f"[{label} indien van toepassing]"
                
                attr_definitions.append(f'    "{key}": "{values_str}"')
            
            attribute_prompt = f"""Gebaseerd op product "{product_keywords}" in categorie "{category_name}":

Genereer Nederlandse Marktplaats attributen gebruik makend van de beschikbare attributen:

{{
  "attributes": {{
{chr(10).join(attr_definitions)}
  }}
}}

Selecteer realistische waarden uit de beschikbare opties. Geef alleen JSON terug."""
        else:
            # Fallback to simple generation
            attribute_prompt = f"""Gebaseerd op product "{product_keywords}" in categorie "{category_name}":

Genereer Nederlandse Marktplaats attributen:

{{
  "attributes": {{
    "conditie": "[Nieuw/Gebruikt/Gereserveerd]",
    "merk": "[merk indien van toepassing]",
    "kleur": "[kleur indien van toepassing]"
  }}
}}

Geef alleen JSON terug."""
        
        try:
            attr_response = bedrock_runtime.invoke_model(
                modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": attribute_prompt}],
                    "max_tokens": 200,
                    "temperature": 0.2
                }),
                contentType="application/json",
                accept="application/json"
            )
            
            attr_body = attr_response["body"].read().decode("utf-8")
            attr_parsed = json.loads(attr_body)
            
            if isinstance(attr_parsed["content"], list):
                attr_text = "".join(part["text"] for part in attr_parsed["content"] if part["type"] == "text").strip()
                
                # Parse attributes JSON
                try:
                    start = attr_text.find('{')
                    end = attr_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = attr_text[start:end]
                        attr_data = json.loads(json_str)
                        attributes = attr_data.get('attributes', {})
                        print(f"✅ Generated attributes: {list(attributes.keys())}")
                    else:
                        attributes = {"conditie": "Gebruikt"}
                except (json.JSONDecodeError, ValueError):
                    attributes = {"conditie": "Gebruikt"}
            else:
                attributes = {"conditie": "Gebruikt"}
                
        except Exception as e:
            print(f"❌ Attribute generation failed: {e}")
            attributes = {"conditie": "Gebruikt"}
    else:
        # Fallback to default category
        print("⚠️  No categories found, using default")
        category_id = 1953
        category_name = "Sport en Fitness"
        attributes = {"conditie": "Gebruikt"}
        suggested_pricing_model = "fixed"  # Default to fixed for unknown categories
    
    # Combine all results
    final_listing = {
        **vision_listing,
        "categoryId": category_id,
        "category": category_name,
        "attributes": attributes,
        "suggestedPricingModel": suggested_pricing_model  # Add pricing model suggestion
    }
    
    # Remove intermediate fields
    final_listing.pop('product_keywords', None)
    
    # Add metadata
    final_listing['_rag_metadata'] = {
        'pinecone_used': True,
        'vision_pinecone_rag': True,
        'images_processed': len(images_data),
        'multi_image_processing': len(images_data) > 1,
        'categories_found': len(categories),
        'best_category_score': categories[0]['score'] if categories else 0,
        'category_found': f"{category_name} ({category_id})",
        'pricing_model_analysis': {
            'suggested_model': suggested_pricing_model,
            'bidding_score': bidding_score if 'bidding_score' in locals() else 0,
            'analysis_performed': True
        }
    }
    
    print(f"✅ Pinecone RAG listing: {final_listing.get('title', 'Unknown')}")
    
    return final_listing


def test_pinecone_rag():
    """Test the Pinecone RAG implementation."""
    
    print("🔧 Testing Pinecone RAG Implementation")
    print("=" * 40)
    
    # Test category search
    test_queries = [
        "kitesurfboard watersport",
        "schommelstoel meubel hout",
        "smartphone mobiel telefoon",
        "fiets elektrisch"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        categories = search_categories(query, top_k=3)
        
        if categories:
            for i, cat in enumerate(categories, 1):
                print(f"   {i}. {cat['categoryName']} (ID: {cat['categoryId']}, score: {cat['score']:.4f})")
        else:
            print("   No categories found")
    
    print("\n✅ Pinecone RAG test completed")


# Backward compatibility - replace the old function
def generate_listing_with_knowledge_base(image_data: bytes, 
                                        rekognition_labels: List[str],
                                        rekognition_text: List[str], 
                                        knowledge_base_id: str) -> Dict[str, Any]:
    """
    Backward compatibility wrapper for Pinecone RAG.
    Note: knowledge_base_id parameter is ignored (no longer needed).
    """
    
    return generate_listing_with_pinecone_rag(
        images_data=[image_data],
        rekognition_labels=rekognition_labels,
        rekognition_text=rekognition_text
    )


if __name__ == "__main__":
    test_pinecone_rag()