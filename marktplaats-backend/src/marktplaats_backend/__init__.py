"""Marktplaats Backend package."""

__version__ = "1.0.0"
__author__ = "Marktplaatser Team"

from .generate_listing_lambda import lambda_handler
from .rekognition_utils import extract_labels_and_text
from .bedrock_utils import generate_listing_with_bedrock
from .category_matcher import (
    fetch_marktplaats_categories,
    flatten_categories,
    match_category_name,
)
from .attribute_mapper import (
    fetch_category_attributes,
    map_ai_attributes_to_marktplaats,
)
from .s3_utils import upload_image_to_s3
from .marktplaats_auth import (
    get_marktplaats_access_token,
    get_authorization_url,
    exchange_code_for_tokens,
    refresh_user_access_token,
)

__all__ = [
    "lambda_handler",
    "extract_labels_and_text",
    "generate_listing_with_bedrock",
    "fetch_marktplaats_categories",
    "flatten_categories",
    "match_category_name",
    "fetch_category_attributes",
    "map_ai_attributes_to_marktplaats",
    "upload_image_to_s3",
    "get_marktplaats_access_token",
    "get_authorization_url",
    "exchange_code_for_tokens",
    "refresh_user_access_token",
]
