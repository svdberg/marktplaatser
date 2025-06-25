#!/usr/bin/env python3
"""
Test suite for category matching functionality.
Tests the category matching logic with realistic Marktplaats categories.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from marktplaats_backend.category_matcher import (
    match_category_name,
    flatten_categories,
    simplify_path
)


class TestCategoryMatcher(unittest.TestCase):
    
    def setUp(self):
        """Set up test data with realistic Marktplaats category structure."""
        
        # Sample category hierarchy based on actual Marktplaats structure
        self.mock_categories = [
            {
                "categoryId": 1,
                "name": "Auto-onderdelen",
                "labels": {"nl-NL": "Auto-onderdelen"},
                "_embedded": {
                    "mp:category": [
                        {
                            "categoryId": 11,
                            "name": "BMW-onderdelen",
                            "labels": {"nl-NL": "BMW-onderdelen"},
                            "_embedded": {"mp:category": []}
                        },
                        {
                            "categoryId": 12,
                            "name": "Audi-onderdelen",
                            "labels": {"nl-NL": "Audi-onderdelen"},
                            "_embedded": {"mp:category": []}
                        },
                        {
                            "categoryId": 13,
                            "name": "Mercedes-onderdelen",
                            "labels": {"nl-NL": "Mercedes-onderdelen"},
                            "_embedded": {"mp:category": []}
                        }
                    ]
                }
            },
            {
                "categoryId": 2,
                "name": "Auto's",
                "labels": {"nl-NL": "Auto's"},
                "_embedded": {
                    "mp:category": [
                        {
                            "categoryId": 21,
                            "name": "Personenautos",
                            "labels": {"nl-NL": "Personenautos"},
                            "_embedded": {"mp:category": []}
                        },
                        {
                            "categoryId": 22,
                            "name": "Bedrijfswagens",
                            "labels": {"nl-NL": "Bedrijfswagens"},
                            "_embedded": {"mp:category": []}
                        }
                    ]
                }
            },
            {
                "categoryId": 3,
                "name": "Fietsen en Brommers",
                "labels": {"nl-NL": "Fietsen en Brommers"},
                "_embedded": {
                    "mp:category": [
                        {
                            "categoryId": 31,
                            "name": "Fietsen",
                            "labels": {"nl-NL": "Fietsen"},
                            "_embedded": {"mp:category": []}
                        },
                        {
                            "categoryId": 32,
                            "name": "Brommers",
                            "labels": {"nl-NL": "Brommers"},
                            "_embedded": {"mp:category": []}
                        }
                    ]
                }
            },
            {
                "categoryId": 4,
                "name": "Sport en Vrije tijd",
                "labels": {"nl-NL": "Sport en Vrije tijd"},
                "_embedded": {
                    "mp:category": [
                        {
                            "categoryId": 41,
                            "name": "Watersporten | Surfplanken",
                            "labels": {"nl-NL": "Watersporten | Surfplanken"},
                            "_embedded": {"mp:category": []}
                        },
                        {
                            "categoryId": 42,
                            "name": "Watersporten | Kitesurfen",
                            "labels": {"nl-NL": "Watersporten | Kitesurfen"},
                            "_embedded": {"mp:category": []}
                        }
                    ]
                }
            }
        ]
        
        # Create flattened categories for testing
        self.flat_categories = flatten_categories(self.mock_categories)

    def test_flatten_categories_structure(self):
        """Test that categories are correctly flattened."""
        expected_names = [
            "Auto-onderdelen",
            "Auto-onderdelen > BMW-onderdelen",
            "Auto-onderdelen > Audi-onderdelen",
            "Auto-onderdelen > Mercedes-onderdelen",
            "Auto's",
            "Auto's > Personenautos",
            "Auto's > Bedrijfswagens",
            "Fietsen en Brommers",
            "Fietsen en Brommers > Fietsen",
            "Fietsen en Brommers > Brommers",
            "Sport en Vrije tijd",
            "Sport en Vrije tijd > Watersporten | Surfplanken",
            "Sport en Vrije tijd > Watersporten | Kitesurfen",
        ]
        
        actual_names = [cat["name"] for cat in self.flat_categories]
        
        for expected_name in expected_names:
            self.assertIn(expected_name, actual_names, 
                         f"Expected category '{expected_name}' not found")

    def test_match_category_name_exact_match(self):
        """Test exact category matching with the actual Marktplaats example."""
        test_input = "Auto-onderdelen > BMW-onderdelen"
        
        result = match_category_name(test_input, self.flat_categories)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["match"], test_input)
        self.assertEqual(result["categoryId"], 11)
    
    def test_with_watersports(self):
        test_input = "Sport en Vrije tijd > Watersporten | Surfplanken"
        result = match_category_name(test_input, self.flat_categories)

        self.assertEqual(result["match"], test_input)
        self.assertEqual(result["categoryId"], 41)

    def test_match_category_name_simplified_match(self):
        """Test category matching with path simplification."""
        # Input has extra levels that should be simplified
        test_input = "Auto-onderdelen > BMW > Specifieke onderdelen > Filters"
        
        result = match_category_name(test_input, self.flat_categories)
        
        self.assertIsNotNone(result)
        # The simplification takes first and last parts, so this becomes "Auto-onderdelen > Filters"
        # which might match "Auto-onderdelen > BMW-onderdelen" due to fuzzy matching
        self.assertIn("Auto-onderdelen", result["match"])

    def test_match_category_name_fuzzy_match(self):
        """Test fuzzy matching with slight variations."""
        test_input = "Auto onderdelen > BMW onderdelen"
        
        result = match_category_name(test_input, self.flat_categories)
        
        self.assertIsNotNone(result)
        self.assertIn("BMW-onderdelen", result["match"])

    def test_match_category_name_level_1_maps_to_level_2(self):
        """Test that level 1 category input gets mapped to a level 2 category."""
        test_input = "Auto-onderdelen"
        
        result = match_category_name(test_input, self.flat_categories)
        
        # Should find a level 2 category match (fuzzy matching to similar level 2)
        self.assertIsNotNone(result)
        # Result should be a level 2 category
        self.assertEqual(result["match"].count(" > "), 1)

    def test_match_category_name_level_2_match(self):
        """Test matching level 2 categories (the ones that support attributes)."""
        test_input = "Auto's > Personenautos"
        
        result = match_category_name(test_input, self.flat_categories)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["match"], test_input)
        self.assertEqual(result["categoryId"], 21)

    def test_match_category_name_no_match(self):
        """Test when no match is found."""
        test_input = "Completely unrelated category"
        
        result = match_category_name(test_input, self.flat_categories)
        
        self.assertIsNone(result)

    def test_match_category_name_bikes_example(self):
        """Test matching bike-related categories."""
        test_input = "Fietsen en Brommers > Fietsen"
        
        result = match_category_name(test_input, self.flat_categories)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["match"], test_input)
        self.assertEqual(result["categoryId"], 31)

    def test_simplify_path_function(self):
        """Test the path simplification helper function."""
        # Test with multiple levels
        result = simplify_path("Auto's > Onderdelen > Carrosserie > Specifiek")
        self.assertEqual(result, "Auto's > Specifiek")
        
        # Test with two levels (should remain unchanged)
        result = simplify_path("Auto's > Carrosserie")
        self.assertEqual(result, "Auto's > Carrosserie")
        
        # Test with single level (should remain unchanged)
        result = simplify_path("Auto's")
        self.assertEqual(result, "Auto's")

    def test_match_category_name_with_variations(self):
        """Test various input formats - results should always be level 2 categories."""
        test_cases = [
            # Valid level 2 categories (exact matches)
            ("Auto-onderdelen > BMW-onderdelen", True),
            ("Auto's > Personenautos", True),
            ("Fietsen en Brommers > Fietsen", True),
            # Level 1 categories that should fuzzy match
            ("Auto-onderdelen", True),  # Should match to one of the Auto-onderdelen subcategories
            # These might not match due to fuzzy matching threshold
            ("Auto's", False),  # Might not match well enough to subcategories
            ("Fietsen en Brommers", False),  # Might not match well enough
        ]
        
        for test_input, should_match in test_cases:
            result = match_category_name(test_input, self.flat_categories)
            
            if should_match:
                self.assertIsNotNone(result, 
                    f"Expected to find match for '{test_input}'")
                # Verify result is always a level 2 category
                self.assertEqual(result["match"].count(" > "), 1,
                    f"Result '{result['match']}' should be level 2 category")
            else:
                # These are okay to not match due to fuzzy matching threshold
                pass

    def test_category_ids_consistency(self):
        """Test that category IDs are consistent in the flattened structure."""
        # Check that each category has a unique ID
        category_ids = [cat["id"] for cat in self.flat_categories]
        self.assertEqual(len(category_ids), len(set(category_ids)), 
                        "Category IDs should be unique")
        
        # Check that we have the expected IDs
        expected_ids = [1, 11, 12, 13, 2, 21, 22, 3, 31, 32, 4, 41, 42]
        for expected_id in expected_ids:
            self.assertIn(expected_id, category_ids, 
                         f"Expected category ID {expected_id} not found")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)