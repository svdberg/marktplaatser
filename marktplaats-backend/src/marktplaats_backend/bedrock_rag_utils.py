"""
RAG-enabled Bedrock utilities using Knowledge Base RetrieveAndGenerate API.

This module combines Claude vision with Knowledge Base retrieval for optimal results:
1. Claude vision analyzes the image for detailed product information
2. Knowledge Base provides relevant categories based on the analysis  
3. Final generation uses both image insights and category context
"""

import boto3
import json
import os
import base64
from typing import List, Dict, Any, Optional

# Force region to eu-west-1
os.environ['AWS_REGION'] = 'eu-west-1'


def generate_listing_with_knowledge_base(image_data: bytes, 
                                        rekognition_labels: List[str],
                                        rekognition_text: List[str], 
                                        knowledge_base_id: str) -> Dict[str, Any]:
    """
    Optimized 2-call approach: Vision + RAG
    1. Claude vision identifies product (SINGLE call)
    2. Knowledge Base RetrieveAndGenerate with product info
    """
    
    print("🚀 Starting optimized 2-call RAG generation...")
    
    # Create Bedrock clients
    session = boto3.Session(region_name="eu-west-1")
    bedrock_runtime = session.client("bedrock-runtime")
    bedrock_agent = session.client("bedrock-agent-runtime")
    
    # Only use Rekognition text if available, ignore poor quality labels
    rekognition_context = ""
    if rekognition_text:
        text_content = ' '.join([text.strip() for text in rekognition_text[:3] if len(text.strip()) > 2])
        if text_content:
            rekognition_context = f"\nDetected text: {text_content}"
    
    print(f"🔍 Using Rekognition text: {rekognition_text if rekognition_text else 'None'}")
    
    # Step 1: Claude vision - get detailed product analysis
    print("👁️  Step 1: Claude vision product analysis...")
    
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    vision_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_base64
            }
        },
        {
            "type": "text",
            "text": f"""Analyze this product image for a Marktplaats listing.{rekognition_context}

Describe the product with these details:
1. Product type (specific: "kitesurfboard", "smartphone", "kinderstoel")
2. Brand/model if visible 
3. Color and condition
4. Key features

Format: "product_type brand model color condition features"
Examples:
- "kitesurfboard Flysurfer Radical blauw gebruikt watersport"
- "smartphone iPhone 12 zwart nieuw electronics"
- "kinderstoel IKEA hout wit gebruikt verstelbaar"

Return only the product description (max 8 words):"""
        }
    ]

    try:
        # Single vision call
        response = bedrock_runtime.invoke_model(
            modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": vision_content}],
                "max_tokens": 50,
                "temperature": 0.1
            }),
            contentType="application/json",
            accept="application/json"
        )

        body = response["body"].read().decode("utf-8")
        parsed = json.loads(body)
        
        if isinstance(parsed["content"], list):
            product_description = "".join(part["text"] for part in parsed["content"] if part["type"] == "text").strip()
            print(f"✅ Product identified: {product_description}")
        else:
            product_description = "unknown product"
            
    except Exception as e:
        print(f"❌ Vision failed: {e}")
        product_description = "unknown product"
    
    # Step 2: Knowledge Base RAG with full listing generation
    print("📚 Step 2: Knowledge Base RAG listing generation...")
    
    try:
        kb_response = bedrock_agent.retrieve_and_generate(
            input={
                'text': f"""Create a complete Dutch Marktplaats listing for: {product_description}

Use your knowledge base to find the exact category and generate:

{{
  "title": "[Dutch title max 60 chars]",
  "description": "[Dutch description 2-3 sentences]", 
  "categoryId": [exact_category_id_from_knowledge_base],
  "category": "[exact_category_name_from_knowledge_base]",
  "attributes": {{
    "condition": "[condition from description]",
    "brand": "[brand if mentioned]",
    "color": "[color if mentioned]"
  }},
  "estimatedPrice": [realistic_euros],
  "priceRange": {{"min": [min], "max": [max]}},
  "priceConfidence": "medium"
}}

Find specific categories like "Kitesurfen" not "Watersport", "Mobiele telefoons" not "Elektronica"."""
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': 'arn:aws:bedrock:eu-west-1:242650470527:inference-profile/eu.anthropic.claude-3-5-sonnet-20240620-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 3,  # Fewer for speed
                            'overrideSearchType': 'SEMANTIC'
                        }
                    },
                    'generationConfiguration': {
                        'inferenceConfig': {
                            'textInferenceConfig': {
                                'maxTokens': 600,
                                'temperature': 0.2
                            }
                        }
                    }
                }
            }
        )
        
        # Extract and parse response
        kb_text = kb_response['output']['text']
        print(f"📝 KB response: {kb_text[:200]}...")
        
        try:
            start = kb_text.find('{')
            end = kb_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = kb_text[start:end]
                listing_data = json.loads(json_str)
                
                print(f"✅ 2-call RAG listing: {listing_data.get('title', 'Unknown')}")
                
                listing_data['_rag_metadata'] = {
                    'knowledge_base_used': True,
                    'two_call_approach': True,
                    'product_identified': product_description,
                    'category_found': f"{listing_data.get('category', 'Unknown')} ({listing_data.get('categoryId', 0)})"
                }
                
                return listing_data
        except Exception as json_error:
            print(f"❌ JSON parsing failed: {json_error}")
        
        # Fallback with basic structure
        return {
            "title": f"{product_description} te koop",
            "description": f"Product in goede staat. {product_description}",
            "categoryId": 1953,
            "category": "Sport en Fitness", 
            "attributes": {"condition": "Gebruikt"},
            "estimatedPrice": 100,
            "priceRange": {"min": 50, "max": 200},
            "priceConfidence": "low"
        }
        
    except Exception as e:
        print(f"❌ Knowledge Base RAG failed: {e}")
        return {
            "title": "Product te koop",
            "description": "Product te koop in goede staat.",
            "categoryId": 1953,
            "category": "Sport en Fitness",
            "attributes": {"condition": "Gebruikt"},
            "estimatedPrice": 50,
            "priceRange": {"min": 25, "max": 100},
            "priceConfidence": "low"
        }


def analyze_image_with_claude_vision(image_data: bytes, 
                                   rekognition_labels: List[str],
                                   rekognition_text: List[str],
                                   bedrock_runtime) -> Dict[str, Any]:
    """Step 1: Use Claude vision to analyze the image and extract product details."""
    
    # Encode image to base64 for Claude vision
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Build context from Rekognition (as supplementary info)
    rekognition_context = ""
    if rekognition_labels or rekognition_text:
        rekognition_context = "\n\nTer referentie, AWS Rekognition heeft ook dit gedetecteerd:"
        if rekognition_labels:
            relevant_labels = [label for label in rekognition_labels[:5] 
                              if isinstance(label, str) and label.lower() not in ['object', 'product']]
            if relevant_labels:
                rekognition_context += f"\n- Labels: {', '.join(relevant_labels)}"
        if rekognition_text:
            text_content = ' '.join(rekognition_text[:3])
            if text_content.strip():
                rekognition_context += f"\n- Tekst: {text_content}"
        rekognition_context += "\n\nGebruik deze informatie aanvullend bij je eigen beeldanalyse."

    # Create message content with image for Claude vision analysis
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_base64
            }
        },
        {
            "type": "text",
            "text": f"""Analyseer deze afbeelding grondig en extract productinformatie voor een Marktplaats advertentie.{rekognition_context}

Geef een gedetailleerde analyse van:
1. Producttype en categorie (specifiek, bijv. "smartphone", "kiteboard", "bank")
2. Merk en model (indien zichtbaar)
3. Kleur(en) en materiaal
4. Staat/conditie (gebaseerd op wat je ziet)
5. Bijzondere kenmerken of details
6. Geschatte afmetingen of specificaties

Return as JSON:
{{
  "product_type": "specifiek producttype",
  "category_keywords": ["keyword1", "keyword2", "keyword3"],
  "brand": "merk indien zichtbaar",
  "model": "model indien zichtbaar", 
  "colors": ["kleur1", "kleur2"],
  "material": "materiaal indien zichtbaar",
  "condition": "staat gebaseerd op afbeelding",
  "features": ["kenmerk1", "kenmerk2"],
  "specifications": "beschrijving van specs/afmetingen",
  "overall_description": "korte beschrijving van het product"
}}"""
        }
    ]

    messages = [{"role": "user", "content": content}]

    try:
        import time
        import random
        
        # Add exponential backoff for throttling - faster for API Gateway timeout
        max_retries = 2  # Reduce retries for faster response
        base_delay = 1   # Shorter delays
        
        for attempt in range(max_retries + 1):
            try:
                response = bedrock_runtime.invoke_model(
                    modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "messages": messages,
                        "max_tokens": 1000,
                        "temperature": 0.3
                    }),
                    contentType="application/json",
                    accept="application/json"
                )
                break  # Success, exit retry loop
            except Exception as e:
                if "ThrottlingException" in str(e) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ Vision analysis throttling, waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(delay)
                    continue
                else:
                    raise  # Re-raise if not throttling or max retries reached

        body = response["body"].read().decode("utf-8")
        parsed = json.loads(body)
        
        # Extract text from Claude response
        if isinstance(parsed["content"], list):
            text = "".join(part["text"] for part in parsed["content"] if part["type"] == "text")
            
            # Parse JSON from response
            try:
                # Handle markdown code blocks
                if "```json" in text:
                    lines = text.split('\n')
                    json_lines = []
                    in_json_block = False
                    for line in lines:
                        if line.strip() == "```json":
                            in_json_block = True
                            continue
                        elif line.strip() == "```" and in_json_block:
                            break
                        elif in_json_block:
                            json_lines.append(line)
                    text = '\n'.join(json_lines)
                
                product_details = json.loads(text)
                print(f"✅ Extracted product details: {product_details.get('product_type', 'Unknown')}")
                return product_details
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON from Claude vision: {e}")
                return {"product_type": "unknown", "category_keywords": [], "overall_description": text}
        
        return {"product_type": "unknown", "category_keywords": []}
        
    except Exception as e:
        print(f"❌ Error in Claude vision analysis: {e}")
        return {"product_type": "unknown", "category_keywords": []}


def query_knowledge_base_for_categories(product_details: Dict[str, Any], 
                                       knowledge_base_id: str,
                                       bedrock_agent) -> Dict[str, Any]:
    """Step 2: Query Knowledge Base to find relevant categories based on product analysis."""
    
    # Build search query from product details
    query_parts = []
    
    if product_details.get('product_type'):
        query_parts.append(f"Product: {product_details['product_type']}")
    
    if product_details.get('category_keywords'):
        keywords = ', '.join(product_details['category_keywords'][:3])
        query_parts.append(f"Keywords: {keywords}")
        
    if product_details.get('brand'):
        query_parts.append(f"Brand: {product_details['brand']}")
        
    search_query = ". ".join(query_parts) if query_parts else "Product category"
    
    try:
        # Use Knowledge Base to find relevant categories
        response = bedrock_agent.retrieve_and_generate(
            input={'text': f"""
Find the best matching Marktplaats categories for this product:

{search_query}

Based on your knowledge base, provide:
1. The top 3 most relevant categories with their IDs
2. Brief explanation of why each category fits
3. The single BEST category recommendation

Return as JSON:
{{
  "best_category": {{
    "id": [category_id],
    "name": "[exact_category_name]",
    "confidence": "high|medium|low"
  }},
  "alternative_categories": [
    {{"id": [id], "name": "[name]", "reason": "[why_it_fits]"}},
    {{"id": [id], "name": "[name]", "reason": "[why_it_fits]"}}
  ],
  "search_query_used": "{search_query}"
}}
"""},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': 'arn:aws:bedrock:eu-west-1:242650470527:inference-profile/eu.anthropic.claude-3-5-sonnet-20240620-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 3,
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                }
            }
        )
        
        print(f"🔍 Knowledge Base response: {response}")
        generated_text = response['output']['text']
        
        # Parse JSON from response
        category_info = extract_json_from_response(generated_text)
        if category_info:
            print(f"✅ Found categories: {category_info.get('best_category', {}).get('name', 'Unknown')}")
            category_info['citations'] = response.get('citations', [])
            return category_info
        else:
            print("⚠️  Could not parse category information from Knowledge Base")
            return {"best_category": {"id": 1953, "name": "Sport en Fitness", "confidence": "low"}}
            
    except Exception as e:
        print(f"❌ Error querying Knowledge Base: {e}")
        return {"best_category": {"id": 1953, "name": "Sport en Fitness", "confidence": "low"}}


def generate_final_listing_with_context(image_data: bytes,
                                       product_details: Dict[str, Any],
                                       category_info: Dict[str, Any],
                                       bedrock_runtime) -> Dict[str, Any]:
    """Step 3: Generate final listing using both image analysis and category context."""
    
    # Encode image to base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Get best category
    best_category = category_info.get('best_category', {})
    
    # Create comprehensive prompt with all context
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64", 
                "media_type": "image/jpeg",
                "data": image_base64
            }
        },
        {
            "type": "text",
            "text": f"""Maak een Marktplaats advertentie voor dit product.

PRODUCT ANALYSE:
{json.dumps(product_details, indent=2, ensure_ascii=False)}

AANBEVOLEN CATEGORIE:
- ID: {best_category.get('id', 0)}
- Naam: {best_category.get('name', 'Algemeen')}
- Vertrouwen: {best_category.get('confidence', 'medium')}

Genereer een complete Marktplaats advertentie:

1. Nederlandse titel (maximaal 60 tekens) - gebruik details uit de afbeelding
2. Nederlandse beschrijving (2-4 zinnen) - beschrijf wat je ziet in de afbeelding
3. Gebruik de aanbevolen categorie (tenzij je een betere suggestie hebt)
4. Attributen gebaseerd op wat je in de afbeelding ziet
5. Realistische prijsschatting voor Nederlandse tweedehands markt

Return as JSON:
{{
  "title": "[Nederlandse titel max 60 chars]",
  "description": "[Nederlandse beschrijving gebaseerd op afbeelding]", 
  "categoryId": {best_category.get('id', 0)},
  "category": "{best_category.get('name', 'Algemeen')}",
  "attributes": {{"brand": "value", "condition": "value", "color": "value"}},
  "estimatedPrice": [prijs in euros],
  "priceRange": {{"min": [min prijs], "max": [max prijs]}},
  "priceConfidence": "high|medium|low"
}}"""
        }
    ]

    messages = [{"role": "user", "content": content}]

    try:
        import time
        import random
        
        # Add exponential backoff for throttling - faster for API Gateway timeout
        max_retries = 2  # Reduce retries for faster response
        base_delay = 1   # Shorter delays
        
        for attempt in range(max_retries + 1):
            try:
                response = bedrock_runtime.invoke_model(
                    modelId="eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "messages": messages,
                        "max_tokens": 1500,
                        "temperature": 0.5
                    }),
                    contentType="application/json",
                    accept="application/json"
                )
                break  # Success, exit retry loop
            except Exception as e:
                if "ThrottlingException" in str(e) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ Throttling detected, waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(delay)
                    continue
                else:
                    raise  # Re-raise if not throttling or max retries reached

        body = response["body"].read().decode("utf-8")
        parsed = json.loads(body)
        
        # Extract text from Claude response
        if isinstance(parsed["content"], list):
            text = "".join(part["text"] for part in parsed["content"] if part["type"] == "text")
            
            # Parse JSON from response
            listing_data = extract_json_from_response(text)
            if listing_data:
                # Ensure categoryId is valid and present
                if not listing_data.get('categoryId') or listing_data.get('categoryId') == 0:
                    listing_data['categoryId'] = best_category.get('id', 1953)
                    listing_data['category'] = best_category.get('name', 'Sport en Fitness')
                print(f"✅ Generated final listing: {listing_data.get('title', 'Unknown')}")
                return listing_data
            else:
                print("❌ Could not parse final listing JSON")
                return create_fallback_listing(product_details, best_category)
        
        return create_fallback_listing(product_details, best_category)
        
    except Exception as e:
        print(f"❌ Error generating final listing: {e}")
        return create_fallback_listing(product_details, best_category)


def extract_json_from_response(content: str) -> Dict[str, Any]:
    """Extract and validate JSON from the generated response."""
    
    try:
        # Handle markdown code blocks
        if "```json" in content:
            lines = content.split('\n')
            json_lines = []
            in_json_block = False
            for line in lines:
                if line.strip() == "```json":
                    in_json_block = True
                    continue
                elif line.strip() == "```" and in_json_block:
                    break
                elif in_json_block:
                    json_lines.append(line)
            content = '\n'.join(json_lines)
        
        # Find JSON block
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = content[start:end]
            return json.loads(json_str)
        else:
            print("❌ No valid JSON found in response")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return {}


def create_fallback_listing(product_details: Dict[str, Any], category: Dict[str, Any]) -> Dict[str, Any]:
    """Create a fallback listing if JSON parsing fails."""
    
    # Ensure we have a valid categoryId - use a safe fallback category
    category_id = category.get('id', 1953)  # Default to Skateboarden en Longboarden as fallback
    if not category_id or category_id == 0:
        category_id = 1953  # Always use a valid category ID
    
    return {
        "title": f"{product_details.get('product_type', 'Product')} te koop",
        "description": product_details.get('overall_description', 'Product te koop in goede staat.'),
        "categoryId": category_id,
        "category": category.get('name', 'Sport en Fitness'),
        "attributes": {
            "condition": product_details.get('condition', 'Gebruikt'),
            "brand": product_details.get('brand', ''),
            "color": ', '.join(product_details.get('colors', []))
        },
        "estimatedPrice": 50,
        "priceRange": {"min": 25, "max": 100},
        "priceConfidence": "low"
    }


# Convenience function that matches the existing API
def generate_listing_with_claude_vision_rag(image_data: bytes, 
                                           rekognition_labels: List[str],
                                           rekognition_text: List[str], 
                                           knowledge_base_id: str) -> Dict[str, Any]:
    """
    Drop-in replacement for generate_listing_with_claude_vision that uses RAG.
    
    This function provides the same interface as the old function but uses
    hybrid Claude vision + Knowledge Base approach for superior results.
    """
    
    return generate_listing_with_knowledge_base(
        image_data=image_data,
        rekognition_labels=rekognition_labels,
        rekognition_text=rekognition_text,
        knowledge_base_id=knowledge_base_id
    )


# Test function to validate Knowledge Base setup
def test_knowledge_base_connection(knowledge_base_id: str) -> bool:
    """Test if the Knowledge Base is properly configured."""
    
    try:
        session = boto3.Session(region_name="eu-west-1")
        bedrock_agent = session.client("bedrock-agent-runtime")
        
        # Simple test query
        response = bedrock_agent.retrieve_and_generate(
            input={'text': 'Find categories for smartphones'},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': 'arn:aws:bedrock:eu-west-1:242650470527:inference-profile/eu.anthropic.claude-3-5-sonnet-20240620-v1:0'
                }
            }
        )
        
        print(f"✅ Knowledge Base test successful")
        print(f"📝 Test response: {response['output']['text'][:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Knowledge Base test failed: {e}")
        return False