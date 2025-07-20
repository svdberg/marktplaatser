#!/usr/bin/env python3
"""
Unit test for the category change fix.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.marktplaats_backend.draft_storage import update_draft, DraftListing


class TestCategoryChangeFix(unittest.TestCase):
    """Test the category change fix that clears attributes."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock existing draft with Kitesurfen category
        self.existing_draft = DraftListing(
            draft_id="test-123",
            user_id="user-456",
            title="Test Kiteboard",
            description="Test description",
            category_id=1404,  # Kitesurfen
            category_name="Kitesurfen",
            attributes=[
                {"key": "condition", "value": "Gebruikt"},
                {"key": "type", "value": "Twin Tip"},
                {"key": "surfaceAreaKite", "value": "12"}
            ],
            price_model={"modelType": "fixed", "askingPrice": 400},
            postcode="1234AB",
            status="draft",
            images=["test.jpg"],
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00",
            ai_generated=True
        )

    @patch('src.marktplaats_backend.draft_storage.get_draft')
    @patch('src.marktplaats_backend.draft_storage.table')
    def test_category_change_clears_attributes(self, mock_table, mock_get_draft):
        """Test that changing category clears attributes."""
        # Mock get_draft to return existing draft
        mock_get_draft.return_value = self.existing_draft
        
        # Mock DynamoDB response
        mock_response = {
            'Attributes': {
                'draftId': {'S': 'test-123'},
                'userId': {'S': 'user-456'},
                'title': {'S': 'Test Kiteboard'},
                'description': {'S': 'Test description'},
                'categoryId': {'N': '1505'},  # Changed to Antiek en Kunst
                'categoryName': {'S': 'Antiek en Kunst'},
                'attributes': {'L': []},  # Should be empty
                'priceModel': {'M': {'modelType': {'S': 'fixed'}, 'askingPrice': {'N': '400'}}},
                'postcode': {'S': '1234AB'},
                'status': {'S': 'draft'},
                'images': {'L': [{'S': 'test.jpg'}]},
                'createdAt': {'S': '2023-01-01T00:00:00'},
                'updatedAt': {'S': '2023-01-01T12:00:00'},
                'aiGenerated': {'BOOL': True}
            }
        }
        mock_table.update_item.return_value = mock_response
        
        # Test updating category
        updates = {
            'categoryId': 1505,  # Change to Antiek en Kunst
            'categoryName': 'Antiek en Kunst > Antiek | Meubels | Stoelen en Banken'
        }
        
        with patch('builtins.print') as mock_print:
            result = update_draft("test-123", "user-456", updates)
            
            # Verify logging message
            mock_print.assert_called_with("Category changed from 1404 to 1505, clearing attributes")
        
        # Verify the function was called with empty attributes
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        
        # Check that attributes were set to empty
        self.assertIn(':attributes', call_args['ExpressionAttributeValues'])
        self.assertEqual(call_args['ExpressionAttributeValues'][':attributes'], [])
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, 1505)
        self.assertEqual(result.attributes, [])

    @patch('src.marktplaats_backend.draft_storage.get_draft')
    @patch('src.marktplaats_backend.draft_storage.table')
    def test_same_category_preserves_attributes(self, mock_table, mock_get_draft):
        """Test that keeping same category preserves attributes."""
        # Mock get_draft to return existing draft
        mock_get_draft.return_value = self.existing_draft
        
        # Mock DynamoDB response
        mock_response = {
            'Attributes': {
                'draftId': {'S': 'test-123'},
                'userId': {'S': 'user-456'},
                'title': {'S': 'Updated Title'},
                'description': {'S': 'Test description'},
                'categoryId': {'N': '1404'},  # Same category
                'categoryName': {'S': 'Kitesurfen'},
                'attributes': {'L': [
                    {'M': {'key': {'S': 'condition'}, 'value': {'S': 'Gebruikt'}}},
                    {'M': {'key': {'S': 'type'}, 'value': {'S': 'Twin Tip'}}},
                    {'M': {'key': {'S': 'surfaceAreaKite'}, 'value': {'S': '12'}}}
                ]},
                'priceModel': {'M': {'modelType': {'S': 'fixed'}, 'askingPrice': {'N': '400'}}},
                'postcode': {'S': '1234AB'},
                'status': {'S': 'draft'},
                'images': {'L': [{'S': 'test.jpg'}]},
                'createdAt': {'S': '2023-01-01T00:00:00'},
                'updatedAt': {'S': '2023-01-01T12:00:00'},
                'aiGenerated': {'BOOL': True}
            }
        }
        mock_table.update_item.return_value = mock_response
        
        # Test updating title only (same category)
        updates = {
            'title': 'Updated Title'
        }
        
        with patch('builtins.print') as mock_print:
            result = update_draft("test-123", "user-456", updates)
            
            # Verify no category change message
            mock_print.assert_not_called()
        
        # Verify attributes were NOT cleared
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        
        # Check that attributes were not modified
        self.assertNotIn(':attributes', call_args['ExpressionAttributeValues'])
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.title, 'Updated Title')
        self.assertEqual(len(result.attributes), 3)

    @patch('src.marktplaats_backend.draft_storage.get_draft')
    @patch('src.marktplaats_backend.draft_storage.table')
    def test_category_change_with_manual_attributes(self, mock_table, mock_get_draft):
        """Test that manually provided attributes override the clearing."""
        # Mock get_draft to return existing draft
        mock_get_draft.return_value = self.existing_draft
        
        # Mock DynamoDB response
        mock_response = {
            'Attributes': {
                'draftId': {'S': 'test-123'},
                'userId': {'S': 'user-456'},
                'title': {'S': 'Test Kiteboard'},
                'description': {'S': 'Test description'},
                'categoryId': {'N': '1505'},  # Changed to Antiek en Kunst
                'categoryName': {'S': 'Antiek en Kunst'},
                'attributes': {'L': [
                    {'M': {'key': {'S': 'urgency'}, 'value': {'S': 'urgency'}}}
                ]},
                'priceModel': {'M': {'modelType': {'S': 'fixed'}, 'askingPrice': {'N': '400'}}},
                'postcode': {'S': '1234AB'},
                'status': {'S': 'draft'},
                'images': {'L': [{'S': 'test.jpg'}]},
                'createdAt': {'S': '2023-01-01T00:00:00'},
                'updatedAt': {'S': '2023-01-01T12:00:00'},
                'aiGenerated': {'BOOL': True}
            }
        }
        mock_table.update_item.return_value = mock_response
        
        # Test updating category with manual attributes
        updates = {
            'categoryId': 1505,
            'categoryName': 'Antiek en Kunst > Antiek | Meubels | Stoelen en Banken',
            'attributes': [{'key': 'urgency', 'value': 'urgency'}]  # Manual override
        }
        
        with patch('builtins.print') as mock_print:
            result = update_draft("test-123", "user-456", updates)
            
            # Should still log the category change
            mock_print.assert_called_with("Category changed from 1404 to 1505, clearing attributes")
        
        # Verify the function was called with the manual attributes (not cleared)
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        
        # Check that manual attributes were used
        self.assertIn(':attributes', call_args['ExpressionAttributeValues'])
        self.assertEqual(call_args['ExpressionAttributeValues'][':attributes'], 
                        [{'key': 'urgency', 'value': 'urgency'}])
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.category_id, 1505)
        self.assertEqual(len(result.attributes), 1)
        self.assertEqual(result.attributes[0]['key'], 'urgency')


if __name__ == '__main__':
    unittest.main()