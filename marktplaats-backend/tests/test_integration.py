#!/usr/bin/env python3
"""
Integration test for the complete attribute mapping pipeline.
Tests the flow: AI attributes -> Marktplaats API format -> Mapped attributes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from marktplaats_backend.attribute_mapper import map_ai_attributes_to_marktplaats


def test_car_listing_integration():
    """Test a complete car listing attribute mapping scenario."""
    
    print("=== Integration Test: Car Listing Attributes ===\n")
    
    # Simulated AI/Bedrock output for a car listing
    ai_generated_attributes = {
        "merk": "Volkswagen",
        "model": "Golf",
        "bouwjaar": "2020", 
        "kilometerstand": "25000",
        "brandstof": "Diesel",
        "transmissie": "Automaat",
        "kleur": "Blauw",
        "aantal_deuren": "5",
        "carrosserie": "Hatchback",
        "prijs": "18500"  # This might not map to any MP attribute
    }
    
    # Simulated Marktplaats API response for "Auto's > Personenautos"
    marktplaats_attributes = [
        {
            "key": "brand",
            "labels": {"nl-NL": "Merk"},
            "type": "LIST",
            "mandatory": True,
            "options": [
                {"key": "volkswagen", "labels": {"nl-NL": "Volkswagen"}},
                {"key": "bmw", "labels": {"nl-NL": "BMW"}},
                {"key": "audi", "labels": {"nl-NL": "Audi"}}
            ]
        },
        {
            "key": "model",
            "labels": {"nl-NL": "Model"},
            "type": "STRING",
            "mandatory": False,
            "options": []
        },
        {
            "key": "year",
            "labels": {"nl-NL": "Bouwjaar"},
            "type": "NUMBER",
            "mandatory": True,
            "options": []
        },
        {
            "key": "mileage",
            "labels": {"nl-NL": "Kilometerstand"},
            "type": "NUMBER",
            "mandatory": True,
            "options": []
        },
        {
            "key": "fuel_type",
            "labels": {"nl-NL": "Brandstof"},
            "type": "LIST",
            "mandatory": True,
            "options": [
                {"key": "petrol", "labels": {"nl-NL": "Benzine"}},
                {"key": "diesel", "labels": {"nl-NL": "Diesel"}},
                {"key": "electric", "labels": {"nl-NL": "Elektrisch"}}
            ]
        },
        {
            "key": "transmission",
            "labels": {"nl-NL": "Transmissie"},
            "type": "LIST",
            "mandatory": False,
            "options": [
                {"key": "manual", "labels": {"nl-NL": "Handgeschakeld"}},
                {"key": "automatic", "labels": {"nl-NL": "Automaat"}}
            ]
        },
        {
            "key": "color",
            "labels": {"nl-NL": "Kleur"},
            "type": "LIST",
            "mandatory": False,
            "options": [
                {"key": "blue", "labels": {"nl-NL": "Blauw"}},
                {"key": "red", "labels": {"nl-NL": "Rood"}},
                {"key": "black", "labels": {"nl-NL": "Zwart"}}
            ]
        },
        {
            "key": "doors",
            "labels": {"nl-NL": "Aantal deuren"},
            "type": "LIST",
            "mandatory": False,
            "options": [
                {"key": "3", "labels": {"nl-NL": "3"}},
                {"key": "5", "labels": {"nl-NL": "5"}}
            ]
        },
        {
            "key": "body_type",
            "labels": {"nl-NL": "Carrosserie"},
            "type": "LIST",
            "mandatory": False,
            "options": [
                {"key": "hatchback", "labels": {"nl-NL": "Hatchback"}},
                {"key": "sedan", "labels": {"nl-NL": "Sedan"}},
                {"key": "suv", "labels": {"nl-NL": "SUV"}}
            ]
        }
    ]
    
    print("INPUT:")
    print("AI Generated Attributes:")
    for key, value in ai_generated_attributes.items():
        print(f"  {key}: {value}")
    
    print(f"\nMarktplaats Available Attributes: {len(marktplaats_attributes)} attributes")
    
    # Perform the mapping
    mapped_attributes = map_ai_attributes_to_marktplaats(
        ai_generated_attributes, 
        marktplaats_attributes
    )
    
    print(f"\nOUTPUT:")
    print(f"Successfully mapped {len(mapped_attributes)} attributes:")
    
    for attr in mapped_attributes:
        # Find the original AI attribute name
        ai_name = next((k for k, v in ai_generated_attributes.items() 
                       if v == attr["value"]), "unknown")
        
        # Find the MP attribute details
        mp_attr = next((mp for mp in marktplaats_attributes 
                       if mp["key"] == attr["key"]), None)
        mp_label = mp_attr["labels"]["nl-NL"] if mp_attr else "unknown"
        is_mandatory = mp_attr["mandatory"] if mp_attr else False
        
        status = "✅ REQUIRED" if is_mandatory else "   optional"
        print(f"  {status} | {ai_name} -> {attr['key']} ({mp_label}) = '{attr['value']}'")
    
    # Check for unmapped attributes
    mapped_values = {attr["value"] for attr in mapped_attributes}
    unmapped = {k: v for k, v in ai_generated_attributes.items() 
                if v not in mapped_values}
    
    if unmapped:
        print(f"\nUnmapped AI attributes ({len(unmapped)}):")
        for key, value in unmapped.items():
            print(f"  ❌ {key}: {value}")
    
    # Check mapping coverage for mandatory fields
    mapped_keys = {attr["key"] for attr in mapped_attributes}
    mandatory_fields = [attr for attr in marktplaats_attributes if attr["mandatory"]]
    missing_mandatory = [attr for attr in mandatory_fields if attr["key"] not in mapped_keys]
    
    if missing_mandatory:
        print(f"\n⚠️  Missing mandatory Marktplaats attributes ({len(missing_mandatory)}):")
        for attr in missing_mandatory:
            label = attr["labels"]["nl-NL"]
            print(f"  {attr['key']}: {label}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Mapped: {len(mapped_attributes)}/{len(ai_generated_attributes)} AI attributes")
    print(f"Mandatory coverage: {len(mandatory_fields) - len(missing_mandatory)}/{len(mandatory_fields)} required fields")
    print(f"Success rate: {len(mapped_attributes)/len(ai_generated_attributes)*100:.1f}%")
    
    # Test assertions for pytest
    assert len(mapped_attributes) >= 8, f"Expected at least 8 mappings, got {len(mapped_attributes)}"
    assert len(missing_mandatory) == 0, f"Missing mandatory fields: {missing_mandatory}"


if __name__ == "__main__":
    test_car_listing_integration()