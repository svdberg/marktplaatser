#!/usr/bin/env python3
"""
Detailed test to see exactly how the attribute mapping works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from marktplaats_backend.attribute_mapper import map_ai_attributes_to_marktplaats

# Sample AI attributes (what Claude/Bedrock might generate)
ai_attributes = {
    "merk": "BMW",
    "model": "3 Serie", 
    "bouwjaar": "2018",
    "kilometerstand": "45000",
    "brandstof": "Benzine",
    "transmissie": "Handgeschakeld",
    "kleur": "Zwart",
    "aantal_deuren": "4",
    "carrosserie": "Sedan"
}

# Sample Marktplaats attributes (from API response)
mp_attributes = [
    {
        "key": "mileage", 
        "labels": {"nl-NL": "Kilometerstand"}, 
        "type": "NUMBER",
        "mandatory": True
    },
    {
        "key": "fuel_type", 
        "labels": {"nl-NL": "Brandstof"}, 
        "type": "LIST",
        "mandatory": True
    },
    {
        "key": "brand", 
        "labels": {"nl-NL": "Merk"}, 
        "type": "LIST",
        "mandatory": True
    },
    {
        "key": "model", 
        "labels": {"nl-NL": "Model"}, 
        "type": "STRING",
        "mandatory": False
    },
    {
        "key": "year", 
        "labels": {"nl-NL": "Bouwjaar"}, 
        "type": "NUMBER",
        "mandatory": True
    },
    {
        "key": "transmission", 
        "labels": {"nl-NL": "Transmissie"}, 
        "type": "LIST",
        "mandatory": False
    },
    {
        "key": "color", 
        "labels": {"nl-NL": "Kleur"}, 
        "type": "LIST",
        "mandatory": False
    },
    {
        "key": "doors", 
        "labels": {"nl-NL": "Aantal deuren"}, 
        "type": "LIST",
        "mandatory": False
    },
    {
        "key": "body_type", 
        "labels": {"nl-NL": "Carrosserie"}, 
        "type": "LIST",
        "mandatory": False
    }
]

print("=== AI Attributes ===")
for key, value in ai_attributes.items():
    print(f"  {key}: {value}")

print("\n=== Marktplaats Attributes ===")
for attr in mp_attributes:
    label = attr["labels"].get("nl-NL", attr.get("name", ""))
    print(f"  {attr["key"]}: {label} ({attr['type']})")

print("\n=== Mapping Results ===")
mapped = map_ai_attributes_to_marktplaats(ai_attributes, mp_attributes)

print(f"Found {len(mapped)} mappings:")
for mapping in mapped:
    # Find the original AI attribute
    ai_attr = next((k for k, v in ai_attributes.items() if v == mapping["value"]), "?")
    # Find the MP attribute
    mp_attr = next((attr for attr in mp_attributes if attr["key"] == mapping["key"]), None)
    mp_label = mp_attr["labels"]["nl-NL"] if mp_attr else "?"
    
    print(f"  AI '{ai_attr}' -> MP '{mapping['key']}' ({mp_label}) = '{mapping['value']}'")

print("\n=== Unmapped AI Attributes ===")
mapped_values = [mapping["value"] for mapping in mapped]
for key, value in ai_attributes.items():
    if value not in mapped_values:
        print(f"  {key}: {value} (not mapped)")

print("\n=== Unmapped MP Attributes ===")
mapped_keys = [mapping["key"] for mapping in mapped]
for attr in mp_attributes:
    if attr["key"] not in mapped_keys:
        label = attr["labels"].get("nl-NL", attr.get("name", ""))
        print(f"  {attr['key']}: {label} (not mapped)")