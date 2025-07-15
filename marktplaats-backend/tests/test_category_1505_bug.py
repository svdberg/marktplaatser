#!/usr/bin/env python3
"""
Unit test for the exact category 1505 bug with real API data.
"""

import unittest
from src.marktplaats_backend.attribute_mapper import map_ai_attributes_to_marktplaats


class TestCategory1505Bug(unittest.TestCase):
    """Test the exact bug scenario with category 1505 and condition attribute."""

    def setUp(self):
        """Set up test with real API data from category 1505."""
        # Real attributes from Marktplaats API for category 1505
        # "Antiek en Kunst > Antiek | Meubels | Stoelen en Banken"
        self.category_1505_attributes = [
            {
                "key": "buyitnow",
                "labels": {"nl-NL": "Direct Kopen"},
                "type": "STRING",
                "options": [{"key": "buyitnow", "labels": {"nl-NL": "Direct Kopen"}}]
            },
            {
                "key": "urgency",
                "labels": {"nl-NL": "Moet nu weg"},
                "type": "STRING",
                "options": [{"key": "urgency", "labels": {"nl-NL": "Moet nu weg"}}]
            },
            {
                "key": "delivery",
                "labels": {"nl-NL": "Levering"},
                "type": "STRING",
                "options": [
                    {"key": "pickup_or_delivery", "labels": {"nl-NL": "Ophalen of Verzenden"}},
                    {"key": "pickup", "labels": {"nl-NL": "Ophalen"}},
                    {"key": "delivery", "labels": {"nl-NL": "Verzenden"}}
                ]
            }
        ]

    def test_category_1505_condition_mapping_should_return_empty(self):
        """Test that condition attribute mapping returns empty array for category 1505."""
        # This is the exact scenario from production logs
        ai_attributes = {"condition": "Gebruikt"}
        
        # Use real API attributes for category 1505
        result = map_ai_attributes_to_marktplaats(ai_attributes, self.category_1505_attributes)
        
        # CRITICAL: Should return empty array since category 1505 doesn't support condition
        self.assertEqual(result, [], 
                        f"Category 1505 should return empty array for condition attribute, got: {result}")
        
        # Verify no condition-related keys in result
        condition_keys = [attr['key'] for attr in result if 'condition' in attr['key'].lower()]
        self.assertEqual(condition_keys, [], 
                        "Should not contain any condition keys in mapped result")

    def test_category_1505_condition_does_not_match_any_attribute(self):
        """Test that 'condition' doesn't fuzzy match any category 1505 attributes."""
        from difflib import get_close_matches
        
        # Get all available labels for category 1505
        mp_labels = [attr.get("labels", {}).get("nl-NL", "") for attr in self.category_1505_attributes]
        
        # Test fuzzy matching
        matches = get_close_matches("condition", mp_labels, n=1, cutoff=0.6)
        
        # Should not match any labels
        self.assertEqual(matches, [], 
                        f"'condition' should not match any labels in category 1505, got: {matches}")

    def test_category_1505_all_valid_attributes_work(self):
        """Test that valid attributes for category 1505 work correctly."""
        # Test mapping valid attributes using DUTCH labels (how the mapper works)
        ai_attributes = {
            "Direct Kopen": "buyitnow",     # Dutch label maps to key
            "Levering": "Ophalen"           # Dutch label with Dutch value
        }
        
        result = map_ai_attributes_to_marktplaats(ai_attributes, self.category_1505_attributes)
        
        # Should successfully map valid attributes
        self.assertEqual(len(result), 2)
        
        # Check Direct Kopen mapping
        buyitnow_attr = next((attr for attr in result if attr["key"] == "buyitnow"), None)
        self.assertIsNotNone(buyitnow_attr)
        self.assertEqual(buyitnow_attr["value"], "buyitnow")  # Should map to key
        
        # Check Levering mapping
        delivery_attr = next((attr for attr in result if attr["key"] == "delivery"), None)
        self.assertIsNotNone(delivery_attr)
        self.assertEqual(delivery_attr["value"], "pickup")  # Should map "Ophalen" to "pickup"

    def test_production_scenario_exact_reproduction(self):
        """Test the exact production scenario that caused the API validation failure."""
        # This is what the AI generated
        ai_attributes = {"condition": "Gebruikt"}
        
        # This is what the mapper should do
        result = map_ai_attributes_to_marktplaats(ai_attributes, self.category_1505_attributes)
        
        # The mapper should return empty array
        self.assertEqual(result, [])
        
        # But production logs show it returned [{'key': 'condition', 'value': 'Gebruikt'}]
        # This proves the bug: the mapper is not filtering out unmappable attributes
        
        # The bug is that when no mapping is found, the original attribute is returned
        # instead of being filtered out
        
        # This test will PASS when the bug is fixed
        # It will FAIL if the bug still exists and returns the original attribute


if __name__ == '__main__':
    unittest.main()