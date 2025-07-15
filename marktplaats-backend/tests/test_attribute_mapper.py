#!/usr/bin/env python3
"""
Unit tests for the attribute mapper module.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.marktplaats_backend.attribute_mapper import (
    map_ai_attributes_to_marktplaats,
    fetch_category_attributes,
    _normalize_ai_attributes
)


class TestAttributeMapper(unittest.TestCase):
    """Test cases for attribute mapping functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock Marktplaats attributes for "Kitesurfen" category (1404)
        self.mock_mp_attributes = [
            {
                "key": "conditie",
                "labels": {"nl-NL": "Conditie"},
                "type": "ENUM",
                "options": [
                    {"key": "nieuw", "labels": {"nl-NL": "Nieuw"}},
                    {"key": "gebruikt", "labels": {"nl-NL": "Gebruikt"}},
                    {"key": "defect", "labels": {"nl-NL": "Defect"}}
                ]
            },
            {
                "key": "merk",
                "labels": {"nl-NL": "Merk"},
                "type": "STRING"
            },
            {
                "key": "kleur",
                "labels": {"nl-NL": "Kleur"},
                "type": "STRING"
            }
        ]

    def test_condition_attribute_mapping_success(self):
        """Test successful mapping of 'condition' to 'conditie'."""
        # AI generates generic 'condition' attribute
        ai_attributes = {
            "condition": "Gebruikt"
        }
        
        # Should map to correct Marktplaats attributes
        result = map_ai_attributes_to_marktplaats(ai_attributes, self.mock_mp_attributes)
        
        # Verify mapping - should get at least the condition
        self.assertGreater(len(result), 0, "Should map at least one attribute")
        
        # Check condition mapping
        condition_attr = next((attr for attr in result if attr["key"] == "conditie"), None)
        self.assertIsNotNone(condition_attr, "Condition should be mapped to 'conditie'")
        self.assertEqual(condition_attr["value"], "gebruikt")

    def test_condition_attribute_mapping_failure(self):
        """Test the validation failure case: 'condition' not valid for category."""
        # Simulate category that doesn't have 'conditie' attribute
        mp_attributes_no_condition = [
            {
                "key": "merk",
                "labels": {"nl-NL": "Merk"},
                "type": "STRING"
            }
        ]
        
        ai_attributes = {
            "condition": "Gebruikt"
        }
        
        result = map_ai_attributes_to_marktplaats(ai_attributes, mp_attributes_no_condition)
        
        # Should skip condition since it's not available
        self.assertEqual(len(result), 0)
        
        # Verify condition is not mapped
        condition_attrs = [attr for attr in result if "conditie" in attr["key"] or "condition" in attr["key"]]
        self.assertEqual(len(condition_attrs), 0, "Condition should not be mapped when not available")

    def test_fuzzy_matching_for_condition(self):
        """Test fuzzy matching for condition-related attributes."""
        ai_attributes = {
            "staat": "gebruikt",  # Dutch for condition
            "toestand": "goed"    # Another Dutch word for condition
        }
        
        result = map_ai_attributes_to_marktplaats(ai_attributes, self.mock_mp_attributes)
        
        # Should fuzzy match both to 'conditie'
        condition_attrs = [attr for attr in result if attr["key"] == "conditie"]
        self.assertTrue(len(condition_attrs) >= 1, "Should fuzzy match condition-related terms")

    def test_invalid_enum_value_handling(self):
        """Test handling of invalid enum values."""
        ai_attributes = {
            "condition": "perfect"  # Invalid value for conditie enum
        }
        
        with patch('builtins.print') as mock_print:
            result = map_ai_attributes_to_marktplaats(ai_attributes, self.mock_mp_attributes)
            
            # Should skip invalid enum value and print warning
            mock_print.assert_called()
            
            # Should return empty since invalid enum is skipped
            self.assertEqual(len(result), 0)

    def test_normalize_ai_attributes_dict(self):
        """Test normalization of dictionary-format AI attributes."""
        ai_dict = {
            "condition": "Gebruikt",
            "brand": "Flysurfer",
            "color": "blauw"
        }
        
        result = _normalize_ai_attributes(ai_dict)
        
        self.assertEqual(len(result), 3)
        self.assertIn({"name": "condition", "value": "Gebruikt"}, result)
        self.assertIn({"name": "brand", "value": "Flysurfer"}, result)
        self.assertIn({"name": "color", "value": "blauw"}, result)

    def test_normalize_ai_attributes_list(self):
        """Test normalization of list-format AI attributes."""
        ai_list = [
            {"name": "condition", "value": "Gebruikt"},
            {"name": "brand", "value": "Flysurfer"}
        ]
        
        result = _normalize_ai_attributes(ai_list)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result, ai_list)

    def test_empty_ai_attributes(self):
        """Test handling of empty AI attributes."""
        result = map_ai_attributes_to_marktplaats({}, self.mock_mp_attributes)
        self.assertEqual(result, [])
        
        result = map_ai_attributes_to_marktplaats([], self.mock_mp_attributes)
        self.assertEqual(result, [])

    def test_empty_mp_attributes(self):
        """Test handling of empty Marktplaats attributes."""
        ai_attributes = {"condition": "Gebruikt"}
        result = map_ai_attributes_to_marktplaats(ai_attributes, [])
        self.assertEqual(result, [])

    @patch('src.marktplaats_backend.attribute_mapper.get_marktplaats_access_token')
    @patch('src.marktplaats_backend.attribute_mapper.requests.get')
    def test_fetch_category_attributes_success(self, mock_get, mock_token):
        """Test successful fetching of category attributes."""
        mock_token.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "fields": self.mock_mp_attributes
        }
        mock_get.return_value = mock_response
        
        flat_categories = [
            {"id": 1000, "name": "Watersport"},
            {"id": 1404, "name": "Watersport > Kitesurfen"}
        ]
        
        result = fetch_category_attributes(1404, flat_categories)
        
        self.assertEqual(result, self.mock_mp_attributes)
        mock_get.assert_called_once()
        
        # Verify correct API call
        args, kwargs = mock_get.call_args
        self.assertIn("categories/1000/1404/attributes", args[0])

    def test_fetch_category_attributes_not_level_2(self):
        """Test error handling for non-level-2 categories."""
        flat_categories = [
            {"id": 1000, "name": "Watersport"},  # Level 1
            {"id": 1500, "name": "Watersport > Kitesurfen > Boards"}  # Level 3
        ]
        
        # Test level 1 category
        with self.assertRaises(ValueError) as context:
            fetch_category_attributes(1000, flat_categories)
        self.assertIn("level 2 categories", str(context.exception))
        
        # Test level 3 category
        with self.assertRaises(ValueError) as context:
            fetch_category_attributes(1500, flat_categories)
        self.assertIn("level 2 categories", str(context.exception))

    def test_real_world_validation_failure_scenario(self):
        """Test the exact scenario from the validation failure."""
        # This is the problematic case where AI generates 'condition' 
        # but the category doesn't support it
        ai_attributes = {
            "condition": "Gebruikt"
        }
        
        # Category that doesn't have condition attribute
        mp_attributes_no_condition = [
            {
                "key": "merk",
                "labels": {"nl-NL": "Merk"},
                "type": "STRING"
            }
        ]
        
        result = map_ai_attributes_to_marktplaats(ai_attributes, mp_attributes_no_condition)
        
        # Should return empty list - no attributes mapped
        self.assertEqual(result, [])
        
        # This would prevent the validation failure in the Marktplaats API
        # because we wouldn't send any unknown attributes


if __name__ == '__main__':
    unittest.main()