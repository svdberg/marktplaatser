"""
Test cases for multi-image functionality.
"""

import json
import base64
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.marktplaats_backend.generate_listing_lambda import (
    _parse_and_validate_request,
    _upload_images_to_s3,
    lambda_handler
)
from src.marktplaats_backend.pinecone_rag_utils import generate_listing_with_pinecone_rag


class TestMultiImageParsing:
    """Test multi-image request parsing and validation."""
    
    def test_single_image_backward_compatibility(self):
        """Test that single image format still works."""
        test_image = base64.b64encode(b"fake_image_data").decode('utf-8')
        
        event = {
            "body": json.dumps({
                "image": test_image,
                "user_id": "test_user",
                "postcode": "1234AB"
            })
        }
        
        result, error = _parse_and_validate_request(event)
        
        assert error is None
        assert result is not None
        assert len(result["images_data"]) == 1
        assert result["images_data"][0] == b"fake_image_data"
        assert result["internal_user_id"] == "test_user"
        assert result["postcode"] == "1234AB"
    
    def test_multiple_images_format(self):
        """Test that multiple images format works."""
        test_images = [
            base64.b64encode(b"fake_image_1").decode('utf-8'),
            base64.b64encode(b"fake_image_2").decode('utf-8'),
            base64.b64encode(b"fake_image_3").decode('utf-8')
        ]
        
        event = {
            "body": json.dumps({
                "images": test_images,
                "user_id": "test_user",
                "postcode": "1234AB"
            })
        }
        
        result, error = _parse_and_validate_request(event)
        
        assert error is None
        assert result is not None
        assert len(result["images_data"]) == 3
        assert result["images_data"][0] == b"fake_image_1"
        assert result["images_data"][1] == b"fake_image_2"
        assert result["images_data"][2] == b"fake_image_3"
    
    def test_maximum_images_validation(self):
        """Test that more than 3 images is rejected."""
        test_images = [
            base64.b64encode(b"fake_image_1").decode('utf-8'),
            base64.b64encode(b"fake_image_2").decode('utf-8'),
            base64.b64encode(b"fake_image_3").decode('utf-8'),
            base64.b64encode(b"fake_image_4").decode('utf-8')  # Too many!
        ]
        
        event = {
            "body": json.dumps({
                "images": test_images,
                "user_id": "test_user"
            })
        }
        
        result, error = _parse_and_validate_request(event)
        
        assert result is None
        assert error is not None
        assert error["statusCode"] == 400
        assert "Maximum 3 images allowed" in json.loads(error["body"])["error"]
    
    def test_empty_images_array(self):
        """Test that empty images array is rejected."""
        event = {
            "body": json.dumps({
                "images": [],
                "user_id": "test_user"
            })
        }
        
        result, error = _parse_and_validate_request(event)
        
        assert result is None
        assert error is not None
        assert error["statusCode"] == 400
        assert "At least one image is required" in json.loads(error["body"])["error"]
    
    def test_missing_image_fields(self):
        """Test that missing both image and images fields is rejected."""
        event = {
            "body": json.dumps({
                "user_id": "test_user"
            })
        }
        
        result, error = _parse_and_validate_request(event)
        
        assert result is None
        assert error is not None
        assert error["statusCode"] == 400
        assert "Either 'image' or 'images' field is required" in json.loads(error["body"])["error"]


class TestS3MultiImageUpload:
    """Test S3 multi-image upload functionality."""
    
    @patch('src.marktplaats_backend.generate_listing_lambda.s3')
    @patch('src.marktplaats_backend.generate_listing_lambda.uuid')
    def test_multiple_images_upload(self, mock_uuid, mock_s3):
        """Test uploading multiple images to S3."""
        # Mock UUID generation
        mock_uuid.uuid4.return_value.hex = 'test-uuid'
        
        # Mock successful S3 upload
        mock_s3.put_object.return_value = None
        
        images_data = [b"image1", b"image2", b"image3"]
        user_id = "test_user"
        
        result = _upload_images_to_s3(images_data, user_id)
        
        assert len(result) == 3
        assert all(url.startswith('https://marktplaatser-images.s3.amazonaws.com/drafts/test_user/') for url in result)
        assert result[0].endswith('test-uuid_img1.jpg')
        assert result[1].endswith('test-uuid_img2.jpg')
        assert result[2].endswith('test-uuid_img3.jpg')
        
        # Verify S3 calls
        assert mock_s3.put_object.call_count == 3
    
    @patch('src.marktplaats_backend.generate_listing_lambda.s3')
    @patch('src.marktplaats_backend.generate_listing_lambda.uuid')
    def test_partial_upload_failure(self, mock_uuid, mock_s3):
        """Test handling of partial upload failures."""
        # Mock UUID generation
        mock_uuid.uuid4.return_value.hex = 'test-uuid'
        
        # Mock S3 upload - second upload fails
        mock_s3.put_object.side_effect = [None, Exception("S3 error"), None]
        
        images_data = [b"image1", b"image2", b"image3"]
        user_id = "test_user"
        
        result = _upload_images_to_s3(images_data, user_id)
        
        # Should get 2 successful uploads (first and third)
        assert len(result) == 2
        assert result[0].endswith('test-uuid_img1.jpg')
        assert result[1].endswith('test-uuid_img3.jpg')


class TestMultiImageAIGeneration:
    """Test AI generation with multiple images."""
    
    @patch('src.marktplaats_backend.pinecone_rag_utils.boto3')
    @patch('src.marktplaats_backend.pinecone_rag_utils.search_categories')
    def test_single_image_processing(self, mock_search, mock_boto3):
        """Test processing with single image (backward compatibility)."""
        # Mock Bedrock responses
        mock_bedrock = Mock()
        mock_boto3.Session().client.return_value = mock_bedrock
        
        mock_vision_response = {
            "body": Mock()
        }
        mock_vision_response["body"].read.return_value = json.dumps({
            "content": [{"type": "text", "text": '{"title": "Test Product", "description": "Test description", "product_keywords": "test product", "estimatedPrice": 100}'}]
        }).encode()
        
        mock_attr_response = {
            "body": Mock()
        }
        mock_attr_response["body"].read.return_value = json.dumps({
            "content": [{"type": "text", "text": '{"attributes": {"conditie": "Nieuw"}}'}]
        }).encode()
        
        mock_bedrock.invoke_model.side_effect = [mock_vision_response, mock_attr_response]
        
        # Mock Pinecone search
        mock_search.return_value = [{
            'categoryId': 1234,
            'categoryName': 'Test Category',
            'score': 0.9,
            'attributes': {}
        }]
        
        result = generate_listing_with_pinecone_rag(
            images_data=[b"fake_image_data"],
            rekognition_labels=["test"],
            rekognition_text=["test text"]
        )
        
        assert result["title"] == "Test Product"
        assert result["categoryId"] == 1234
        assert result["_rag_metadata"]["images_processed"] == 1
        assert result["_rag_metadata"]["multi_image_processing"] == False
    
    @patch('src.marktplaats_backend.pinecone_rag_utils.boto3')
    @patch('src.marktplaats_backend.pinecone_rag_utils.search_categories')
    def test_multiple_image_processing(self, mock_search, mock_boto3):
        """Test processing with multiple images."""
        # Mock Bedrock responses
        mock_bedrock = Mock()
        mock_boto3.Session().client.return_value = mock_bedrock
        
        mock_vision_response = {
            "body": Mock()
        }
        mock_vision_response["body"].read.return_value = json.dumps({
            "content": [{"type": "text", "text": '{"title": "Multi-angle Product", "description": "Enhanced description from multiple views", "product_keywords": "detailed product analysis", "estimatedPrice": 150}'}]
        }).encode()
        
        mock_attr_response = {
            "body": Mock()
        }
        mock_attr_response["body"].read.return_value = json.dumps({
            "content": [{"type": "text", "text": '{"attributes": {"conditie": "Gebruikt", "kleur": "Blauw"}}'}]
        }).encode()
        
        mock_bedrock.invoke_model.side_effect = [mock_vision_response, mock_attr_response]
        
        # Mock Pinecone search
        mock_search.return_value = [{
            'categoryId': 5678,
            'categoryName': 'Enhanced Category',
            'score': 0.95,
            'attributes': {}
        }]
        
        result = generate_listing_with_pinecone_rag(
            images_data=[b"image1", b"image2", b"image3"],
            rekognition_labels=["test"],
            rekognition_text=["test text"]
        )
        
        assert result["title"] == "Multi-angle Product"
        assert result["categoryId"] == 5678
        assert result["_rag_metadata"]["images_processed"] == 3
        assert result["_rag_metadata"]["multi_image_processing"] == True
    
    def test_backward_compatibility_parameter(self):
        """Test that the old image_data parameter still works."""
        with patch('src.marktplaats_backend.pinecone_rag_utils.boto3'):
            with patch('src.marktplaats_backend.pinecone_rag_utils.search_categories') as mock_search:
                mock_search.return_value = []
                
                # Should not raise an error
                result = generate_listing_with_pinecone_rag(
                    image_data=b"single_image",
                    rekognition_labels=[],
                    rekognition_text=[]
                )
                
                assert result["_rag_metadata"]["images_processed"] == 1
                assert result["_rag_metadata"]["multi_image_processing"] == False


class TestEndToEndMultiImage:
    """Test end-to-end multi-image functionality."""
    
    @patch('src.marktplaats_backend.generate_listing_lambda.create_draft_from_ai_generation')
    @patch('src.marktplaats_backend.generate_listing_lambda._upload_images_to_s3')
    @patch('src.marktplaats_backend.generate_listing_lambda.generate_listing_with_pinecone_rag')
    @patch('src.marktplaats_backend.generate_listing_lambda.extract_labels_and_text')
    @patch('src.marktplaats_backend.generate_listing_lambda.fetch_marktplaats_categories')
    @patch('src.marktplaats_backend.generate_listing_lambda.flatten_categories')
    @patch('src.marktplaats_backend.generate_listing_lambda.get_user_token')
    @patch('src.marktplaats_backend.generate_listing_lambda.get_marktplaats_user_id')
    def test_lambda_handler_multi_image(self, mock_get_user_id, mock_get_token, mock_flatten, 
                                       mock_fetch_cats, mock_extract, mock_generate, 
                                       mock_upload, mock_create_draft):
        """Test full Lambda handler with multiple images."""
        # Setup mocks
        mock_get_token.return_value = "fake_token"
        mock_get_user_id.return_value = "mp_user_123"
        mock_flatten.return_value = [{"id": 1234, "name": "Test Category"}]
        mock_fetch_cats.return_value = []
        mock_extract.return_value = (["label1"], ["text1"])
        
        mock_generate.return_value = {
            "title": "Multi-image Listing",
            "description": "Generated from multiple images",
            "categoryId": 1234,
            "estimatedPrice": 200,
            "priceRange": {"min": 180, "max": 220},
            "priceConfidence": "high"
        }
        
        mock_upload.return_value = ["url1", "url2", "url3"]
        
        mock_draft = Mock()
        mock_draft.draft_id = "draft_123"
        mock_draft.title = "Multi-image Listing"
        mock_draft.description = "Generated from multiple images"
        mock_draft.category_id = 1234
        mock_draft.category_name = "Test Category"
        mock_create_draft.return_value = mock_draft
        
        # Test event with multiple images
        test_images = [
            base64.b64encode(b"image1").decode('utf-8'),
            base64.b64encode(b"image2").decode('utf-8'),
            base64.b64encode(b"image3").decode('utf-8')
        ]
        
        event = {
            "body": json.dumps({
                "images": test_images,
                "user_id": "internal_user_123",
                "postcode": "1234AB"
            })
        }
        
        result = lambda_handler(event, {})
        
        # Verify success
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["draftId"] == "draft_123"
        assert response_data["title"] == "Multi-image Listing"
        
        # Verify that upload was called with multiple images
        mock_upload.assert_called_once()
        uploaded_images = mock_upload.call_args[0][0]
        assert len(uploaded_images) == 3
        
        # Verify AI generation was called with multiple images
        mock_generate.assert_called_once()
        ai_images = mock_generate.call_args[1]["images_data"]
        assert len(ai_images) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])