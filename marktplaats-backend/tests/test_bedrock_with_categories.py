#!/usr/bin/env python3
"""
Test the new Bedrock function that includes category list in the prompt.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from marktplaats_backend.bedrock_utils import _filter_categories_for_claude


class TestBedrockWithCategories(unittest.TestCase):
    
    def setUp(self):
        """Set up test data with sample categories."""
        self.sample_categories = [
            {"name": "Auto-onderdelen", "id": 1},  # Level 1
            {"name": "Auto-onderdelen > BMW-onderdelen", "id": 11},  # Level 2
            {"name": "Auto-onderdelen > Audi-onderdelen", "id": 12},  # Level 2
            {"name": "Auto's", "id": 2},  # Level 1
            {"name": "Auto's > Personenautos", "id": 21},  # Level 2
            {"name": "Auto's > Personenautos > BMW", "id": 211},  # Level 3
            {"name": "Fietsen en Brommers", "id": 3},  # Level 1
            {"name": "Fietsen en Brommers > Fietsen", "id": 31},  # Level 2
            {"name": "Huis en Inrichting", "id": 4},  # Level 1
            {"name": "Huis en Inrichting > Meubels", "id": 41},  # Level 2
        ]

    def test_filter_categories_for_claude(self):
        """Test that only level 2 categories are returned."""
        filtered = _filter_categories_for_claude(self.sample_categories)
        
        # Should only have level 2 categories (exactly one '>')
        expected_names = [
            "Auto-onderdelen > Audi-onderdelen",
            "Auto-onderdelen > BMW-onderdelen", 
            "Auto's > Personenautos",
            "Fietsen en Brommers > Fietsen",
            "Huis en Inrichting > Meubels"
        ]
        
        actual_names = [cat['name'] for cat in filtered]
        self.assertEqual(sorted(actual_names), sorted(expected_names))

    def test_filter_categories_max_limit(self):
        """Test that the max_categories limit is respected."""
        # Create more categories than the limit
        many_categories = []
        for i in range(60):
            many_categories.append({
                "name": f"Category {i} > Subcategory {i}",
                "id": i
            })
        
        filtered = _filter_categories_for_claude(many_categories, max_categories=10)
        self.assertEqual(len(filtered), 10)

    def test_filter_categories_sorting(self):
        """Test that categories are sorted alphabetically."""
        filtered = _filter_categories_for_claude(self.sample_categories)
        
        names = [cat['name'] for cat in filtered]
        self.assertEqual(names, sorted(names))

    def test_filter_categories_level_filtering(self):
        """Test that only level 2 categories are included."""
        filtered = _filter_categories_for_claude(self.sample_categories)
        
        for cat in filtered:
            # Should have exactly one '>' (level 2)
            self.assertEqual(cat['name'].count(' > '), 1, 
                           f"Category '{cat['name']}' is not level 2")

    def test_empty_categories_list(self):
        """Test behavior with empty category list."""
        filtered = _filter_categories_for_claude([])
        self.assertEqual(len(filtered), 0)

    def test_no_level_2_categories(self):
        """Test behavior when no level 2 categories exist."""
        level_1_only = [
            {"name": "Category 1", "id": 1},
            {"name": "Category 2", "id": 2}
        ]
        
        filtered = _filter_categories_for_claude(level_1_only)
        self.assertEqual(len(filtered), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)