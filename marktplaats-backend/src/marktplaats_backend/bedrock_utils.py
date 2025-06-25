import boto3
import json


def generate_listing_with_bedrock(labels, text_lines):
    bedrock = boto3.client("bedrock-runtime")

    messages = [
    {
        "role": "user",
        "content": f"""
Je bent een assistent die gebruikers helpt met het maken van Marktplaats-advertenties voor tweedehands producten.

Gebaseerd op de volgende beeldanalyse:
- Gedetecteerde labels: {", ".join(labels)}
- Gedetecteerde tekst: {", ".join(text_lines)}

Genereer:
1. Een beknopte Nederlandse titel (maximaal 80 tekens)
2. Een Nederlandse productbeschrijving van 2–4 zinnen
3. Een suggestie voor de juiste Marktplaats-categorie
4. Relevante attributen als key-value paren (zoals merk, staat, leeftijdscategorie, materiaal, enz.)

Geef het resultaat terug als JSON met de sleutels: title, description, category, attributes.
"""
    }
    ]
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": 600,
            "temperature": 0.7
        }),
        contentType="application/json",
        accept="application/json"
    )

    body = response["body"].read().decode("utf-8")
    parsed = json.loads(body)

    # Claude returns content as a list of message parts
    if isinstance(parsed["content"], list):
        text = "".join(part["text"] for part in parsed["content"] if part["type"] == "text")
        return json.loads(text)

    raise ValueError("Claude returned unexpected content structure")
