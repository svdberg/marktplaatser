import boto3
import json
import os

# Force region to eu-west-1
os.environ['AWS_REGION'] = 'eu-west-1'


def _filter_categories_for_claude(categories, max_categories=2105):
    """Filter categories to only include level 2 (attribute-supporting) categories."""
    # Get only level 2 categories (exactly one '>' separator)
    level_2_categories = [
        cat for cat in categories 
        if cat['name'].count(' > ') == 1
    ]
    
    # Sort by name for consistency and take the first max_categories
    level_2_categories.sort(key=lambda x: x['name'])
    return level_2_categories[:max_categories]


def generate_listing_with_bedrock(labels, text_lines, available_categories=None):
    # Create session with explicit region
    session = boto3.Session(region_name="eu-west-1")
    bedrock = session.client("bedrock-runtime")

    # Format categories for the prompt
    category_text = ""
    if available_categories:
        # Filter to level 2 categories only (these support attributes)
        filtered_categories = _filter_categories_for_claude(available_categories)
        
        category_text = f"\n\nBeschikbare Marktplaats categorieën ({len(filtered_categories)} opties):\n"
        for cat in filtered_categories:
            category_text += f"- {cat['name']}\n"
        category_text += "\nKies EXACT één van bovenstaande categorieën die het beste past bij het product."
    else:
        category_text = "\n3. Een suggestie voor de juiste Marktplaats-categorie"

    messages = [
    {
        "role": "user",
        "content": f"""
Je bent een assistent die gebruikers helpt met het maken van Marktplaats-advertenties voor tweedehands producten.

Gebaseerd op de volgende beeldanalyse:
- Gedetecteerde labels: {", ".join(labels)}
- Gedetecteerde tekst: {", ".join(text_lines)}
{category_text}

Genereer:
1. Een beknopte Nederlandse titel (maximaal 80 tekens)
2. Een Nederlandse productbeschrijving van 2–4 zinnen
3. De juiste categorie (kies EXACT uit de lijst hierboven)
4. Relevante attributen als key-value paren (zoals merk, staat, leeftijdscategorie, materiaal, enz.)

Geef het resultaat terug als JSON met de sleutels: title, description, category, attributes.
De category moet EXACT overeenkomen met één van de opgegeven categorieën.
"""
    }
    ]
    response = bedrock.invoke_model(
        modelId="eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }),
        contentType="application/json",
        accept="application/json"
    )

    body = response["body"].read().decode("utf-8")
    print(f"Raw response body: {body}")
    parsed = json.loads(body)
    print(f"Parsed response: {json.dumps(parsed, indent=2)}")

    # Claude returns content as a list of message parts
    if isinstance(parsed["content"], list):
        text = "".join(part["text"] for part in parsed["content"] if part["type"] == "text")
        print(f"Extracted text from Claude: '{text}'")
        if not text.strip():
            raise ValueError("Claude returned empty response")
        
        # Claude 3.7 sometimes wraps JSON in markdown code blocks
        if "```json" in text:
            # Extract JSON from markdown code block
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
            print(f"Extracted JSON from code block: '{text}'")
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from Claude: {text}")
            raise ValueError(f"Claude returned invalid JSON: {e}")

    raise ValueError("Claude returned unexpected content structure")
