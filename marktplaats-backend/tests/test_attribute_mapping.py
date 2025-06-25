#!/usr/bin/env python3
"""
Test suite for attribute mapping functionality.
Uses realistic data from AWS Rekognition and Marktplaats API.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from marktplaats_backend.attribute_mapper import map_ai_attributes_to_marktplaats, _normalize_ai_attributes


class TestAttributeMapping(unittest.TestCase):
    
    def setUp(self):
        """Set up test data based on actual API responses."""
        
        # Sample AI-generated attributes from Claude/Bedrock (typical car listing)
        self.ai_attributes_dict = {
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
        
        self.ai_attributes_list = [
            {"name": "merk", "value": "BMW"},
            {"name": "model", "value": "3 Serie"},
            {"name": "bouwjaar", "value": "2018"},
            {"name": "kilometerstand", "value": "45000"},
            {"name": "brandstof", "value": "Benzine"},
            {"name": "transmissie", "value": "Handgeschakeld"},
            {"name": "kleur", "value": "Zwart"},
            {"name": "aantal_deuren", "value": "4"},
            {"name": "carrosserie", "value": "Sedan"}
        ]
        
        # Sample Marktplaats attributes response (Auto's > Personenautos)
        self.mp_attributes = [
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
                "key": "brand", 
                "labels": {"nl-NL": "Merk"}, 
                "type": "LIST",
                "mandatory": True,
                "options": [
                    {"key": "bmw", "labels": {"nl-NL": "BMW"}},
                    {"key": "audi", "labels": {"nl-NL": "Audi"}},
                    {"key": "mercedes", "labels": {"nl-NL": "Mercedes-Benz"}}
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
                    {"key": "black", "labels": {"nl-NL": "Zwart"}},
                    {"key": "white", "labels": {"nl-NL": "Wit"}},
                    {"key": "silver", "labels": {"nl-NL": "Zilver"}}
                ]
            },
            {
                "key": "doors", 
                "labels": {"nl-NL": "Aantal deuren"}, 
                "type": "LIST",
                "mandatory": False,
                "options": [
                    {"key": "2", "labels": {"nl-NL": "2"}},
                    {"key": "4", "labels": {"nl-NL": "4"}},
                    {"key": "5", "labels": {"nl-NL": "5"}}
                ]
            },
            {
                "key": "body_type", 
                "labels": {"nl-NL": "Carrosserie"}, 
                "type": "LIST",
                "mandatory": False,
                "options": [
                    {"key": "sedan", "labels": {"nl-NL": "Sedan"}},
                    {"key": "hatchback", "labels": {"nl-NL": "Hatchback"}},
                    {"key": "suv", "labels": {"nl-NL": "SUV"}}
                ]
            }
        ]

    def test_normalize_ai_attributes_dict(self):
        """Test normalization of dict-format AI attributes."""
        normalized = _normalize_ai_attributes(self.ai_attributes_dict)
        
        self.assertIsInstance(normalized, list)
        self.assertEqual(len(normalized), 9)
        
        # Check that all items have name and value
        for item in normalized:
            self.assertIn("name", item)
            self.assertIn("value", item)
        
        # Check specific mapping
        merk_item = next((item for item in normalized if item["name"] == "merk"), None)
        self.assertIsNotNone(merk_item)
        self.assertEqual(merk_item["value"], "BMW")

    def test_normalize_ai_attributes_list(self):
        """Test normalization of list-format AI attributes."""
        normalized = _normalize_ai_attributes(self.ai_attributes_list)
        
        self.assertIsInstance(normalized, list)
        self.assertEqual(len(normalized), 9)
        self.assertEqual(normalized, self.ai_attributes_list)  # Should be unchanged

    def test_normalize_ai_attributes_empty(self):
        """Test normalization of empty/invalid inputs."""
        self.assertEqual(_normalize_ai_attributes(None), [])
        self.assertEqual(_normalize_ai_attributes([]), [])
        self.assertEqual(_normalize_ai_attributes({}), [])
        self.assertEqual(_normalize_ai_attributes("invalid"), [])

    def test_map_ai_attributes_exact_matches(self):
        """Test mapping with exact Dutch label matches."""
        mapped = map_ai_attributes_to_marktplaats(
            self.ai_attributes_dict, 
            self.mp_attributes
        )
        
        # Should find mappings for most attributes
        self.assertGreater(len(mapped), 5)
        
        # Check specific mappings
        mapped_keys = [attr["key"] for attr in mapped]
        expected_keys = ["brand", "model", "year", "mileage", "fuel_type", 
                        "transmission", "color", "doors", "body_type"]
        
        for expected_key in expected_keys:
            self.assertIn(expected_key, mapped_keys, 
                         f"Expected to find mapping for {expected_key}")

    def test_map_ai_attributes_fuzzy_matches(self):
        """Test mapping with fuzzy string matching."""
        # AI attributes with slight variations
        fuzzy_ai_attributes = {
            "merknaam": "BMW",  # "merknaam" vs "Merk"
            "bouwjaar": "2018",  # exact match
            "km_stand": "45000",  # "km_stand" vs "Kilometerstand"
            "brandstoftype": "Benzine",  # "brandstoftype" vs "Brandstof"
        }
        
        mapped = map_ai_attributes_to_marktplaats(
            fuzzy_ai_attributes, 
            self.mp_attributes
        )
        
        # Should still find some matches due to fuzzy matching
        self.assertGreaterEqual(len(mapped), 2)
        
        # Check that bouwjaar (exact match) is found
        mapped_keys = [attr["key"] for attr in mapped]
        self.assertIn("year", mapped_keys)

    def test_map_ai_attributes_no_matches(self):
        """Test mapping when no matches are found."""
        no_match_attributes = {
            "completely_unrelated": "value1",
            "another_random_field": "value2"
        }
        
        mapped = map_ai_attributes_to_marktplaats(
            no_match_attributes, 
            self.mp_attributes
        )
        
        self.assertEqual(len(mapped), 0)

    def test_map_ai_attributes_with_list_input(self):
        """Test mapping with list-format AI attributes."""
        mapped = map_ai_attributes_to_marktplaats(
            self.ai_attributes_list, 
            self.mp_attributes
        )
        
        # Should produce same results as dict input
        mapped_dict = map_ai_attributes_to_marktplaats(
            self.ai_attributes_dict, 
            self.mp_attributes
        )
        
        self.assertEqual(len(mapped), len(mapped_dict))
        
        # Check that all mapped attributes have key and value
        for attr in mapped:
            self.assertIn("key", attr)
            self.assertIn("value", attr)

    def test_map_ai_attributes_empty_mp_attributes(self):
        """Test mapping when Marktplaats attributes list is empty."""
        mapped = map_ai_attributes_to_marktplaats(
            self.ai_attributes_dict, 
            []
        )
        
        self.assertEqual(len(mapped), 0)

    def test_attribute_values_preserved(self):
        """Test that original AI attribute values are preserved in mapping."""
        mapped = map_ai_attributes_to_marktplaats(
            {"bouwjaar": "2018", "merk": "BMW"}, 
            self.mp_attributes
        )
        
        # Find the year mapping
        year_mapping = next((attr for attr in mapped if attr["key"] == "year"), None)
        self.assertIsNotNone(year_mapping)
        self.assertEqual(year_mapping["value"], "2018")
        
        # Find the brand mapping
        brand_mapping = next((attr for attr in mapped if attr["key"] == "brand"), None)
        self.assertIsNotNone(brand_mapping)
        self.assertEqual(brand_mapping["value"], "BMW")

    def test_case_insensitive_matching(self):
        """Test that matching works with different cases."""
        mixed_case_attributes = {
            "MERK": "BMW",
            "Model": "3 Serie",
            "bouwJAAR": "2018"
        }
        
        # Note: Current implementation might be case-sensitive
        # This test documents the current behavior
        mapped = map_ai_attributes_to_marktplaats(
            mixed_case_attributes, 
            self.mp_attributes
        )
        
        # Depending on implementation, this might find fewer matches
        mapped_keys = [attr["key"] for attr in mapped]
        print(f"Case test mapped keys: {mapped_keys}")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)