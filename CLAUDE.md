# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a serverless AWS Lambda application for generating marketplace listings from images. The system processes uploaded images through AWS Rekognition for object detection and text extraction, then uses AWS Bedrock to generate structured listing data that matches Marktplaats categories and attributes.

**Core Components:**
- `src/marktplaats_backend/generate_listing_lambda.py` - Main Lambda handler
- `src/marktplaats_backend/rekognition_utils.py` - AWS Rekognition integration
- `src/marktplaats_backend/bedrock_utils.py` - AWS Bedrock/Claude integration
- `src/marktplaats_backend/category_matcher.py` - Marktplaats category matching
- `src/marktplaats_backend/attribute_mapper.py` - Attribute mapping to Marktplaats format
- `src/marktplaats_backend/s3_utils.py` - S3 operations
- `src/marktplaats_backend/marktplaats_auth.py` - Marktplaats API authentication

**Data Flow:**
1. Lambda receives base64-encoded image via HTTP POST
2. Fetch Marktplaats categories from API (level 2 categories that support attributes)
3. Rekognition analyzes image for labels and text
4. Bedrock generates listing with category list as input (exact category selection)
5. AI attributes are mapped to Marktplaats attribute schema
6. Structured JSON response returned to client

## Project Structure

```
marktplaats-backend/
├── src/marktplaats_backend/     # Source code package
├── tests/                       # Test files
├── deploy.sh                    # Deployment script
├── test.sh                      # Test script
├── serverless.yaml              # Serverless config
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
└── pyproject.toml              # Modern Python config
```

## Development Commands

**Install dependencies:**
```bash
cd marktplaats-backend
pip install -r requirements.txt
# For development
pip install -e ".[dev]"
```

**Run tests:**
```bash
# All tests
python -m pytest tests/ -v
# Specific test
python tests/test_attribute_mapping.py
python tests/test_integration.py
```

**Code quality:**
```bash
flake8 src/ tests/
black src/ tests/
mypy src/
```

**Deploy to AWS:**
```bash
export MARKTPLAATS_CLIENT_ID=your_client_id
export MARKTPLAATS_CLIENT_SECRET=your_client_secret
cd marktplaats-backend
./deploy.sh
```

**Test the deployed function:**
```bash
cd marktplaats-backend
./test.sh sample.jpg
```

**Local testing:**
```bash
cd marktplaats-backend
serverless invoke local -f generateListing
```

## Deployment & Infrastructure

The application uses Serverless Framework for deployment configuration (`serverless.yaml`):
- Runtime: Python 3.11
- Region: eu-west-1
- Memory: 512MB
- Timeout: 30s
- HTTP endpoint: POST `/generate-listing`

**Required AWS permissions:**
- Rekognition: DetectLabels, DetectText
- S3: PutObject, GetObject, ListBucket
- Bedrock: InvokeModel

## Configuration

**Environment Variables:**
- `MARKTPLAATS_CLIENT_ID` - Marktplaats API client ID
- `MARKTPLAATS_CLIENT_SECRET` - Marktplaats API client secret
- `S3_BUCKET` - S3 bucket name (marktplaatser-images)

**Key Implementation Notes:**
- Marktplaats API attributes only work for level 2 categories
- API response uses "fields" array with "key" identifiers
- Categories are provided to Claude for exact selection (no fuzzy matching needed)
- Only level 2 categories are sent to Claude (filtered from full list)
- Fuzzy string matching with 0.6 cutoff for attribute mapping
- Proper relative imports using dot notation in source code

## Next Steps and Improvements

- Snapshot this, pivot to using the image directly in Claude Sonnet 3.7 for recognition and description. Do this next to the kognition input.
- Snapshot for full working implementation.

## TODO List

- Implement full integration of AWS Bedrock with Claude Sonnet 3.7
- Create comprehensive test suite for image recognition and listing generation
- Develop more robust category and attribute mapping
- Optimize AWS Lambda function performance
- Add error handling and logging mechanisms
- Explore potential for multi-language support
- Investigate caching strategies for API calls and model responses