# Marktplaats Backend

AWS Lambda application for generating marketplace listings from images using AI.

## Overview

This serverless application processes uploaded images through AWS Rekognition for object detection and text extraction, then uses AWS Bedrock to generate structured listing data that matches Marktplaats categories and attributes.

## Architecture

```
Image Upload → AWS Rekognition → AWS Bedrock → Marktplaats API → Structured Listing
```

### Core Components

- **`generate_listing_lambda.py`** - Main Lambda handler
- **`rekognition_utils.py`** - AWS Rekognition integration 
- **`bedrock_utils.py`** - AWS Bedrock/Claude integration
- **`category_matcher.py`** - Marktplaats category matching
- **`attribute_mapper.py`** - Attribute mapping to Marktplaats format
- **`s3_utils.py`** - S3 operations
- **`marktplaats_auth.py`** - Marktplaats API authentication

## Setup

### Prerequisites

- Python 3.11+
- AWS CLI configured
- Serverless Framework
- Node.js (for Serverless)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Serverless dependencies  
npm install

# Set environment variables
export MARKTPLAATS_CLIENT_ID=your_client_id
export MARKTPLAATS_CLIENT_SECRET=your_client_secret
```

### Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Run linting
flake8 src/ tests/
black src/ tests/
```

## Deployment

```bash
# Deploy to AWS
./deploy.sh
```

This script:
1. Creates S3 bucket if needed
2. Deploys the serverless stack
3. Outputs the API endpoint to `endpoint.txt`

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific functionality
python tests/test_attribute_mapping.py
python tests/test_integration.py

# Test deployed endpoint
./test.sh sample.jpg
```

## Project Structure

```
marktplaats-backend/
├── src/marktplaats_backend/     # Source code
│   ├── __init__.py
│   ├── generate_listing_lambda.py
│   ├── rekognition_utils.py
│   ├── bedrock_utils.py
│   ├── category_matcher.py
│   ├── attribute_mapper.py
│   ├── s3_utils.py
│   └── marktplaats_auth.py
├── tests/                       # Test files
│   ├── __init__.py
│   ├── test_attribute_mapping.py
│   ├── test_integration.py
│   └── test_detailed_mapping.py
├── deploy.sh                    # Deployment script
├── test.sh                      # Test script
├── serverless.yaml              # Serverless config
├── requirements.txt             # Python dependencies
├── package.json                 # Node.js dependencies
├── setup.py                     # Package setup
└── pyproject.toml              # Modern Python config
```

## Configuration

### Environment Variables

- `MARKTPLAATS_CLIENT_ID` - Marktplaats API client ID
- `MARKTPLAATS_CLIENT_SECRET` - Marktplaats API client secret
- `S3_BUCKET` - S3 bucket for image storage

### AWS Resources

- **Lambda Function**: Processes image upload requests
- **S3 Bucket**: Stores uploaded images
- **IAM Role**: Permissions for Rekognition, Bedrock, S3

## API Usage

### POST /generate-listing

Upload an image to generate a Marktplaats listing.

**Request:**
```json
{
  "image": "base64-encoded-image-data"
}
```

**Response:**
```json
{
  "title": "Generated listing title",
  "description": "Generated description", 
  "categoryId": 123,
  "categoryName": "Category > Subcategory",
  "attributes": [
    {"key": "brand", "value": "BMW"},
    {"key": "year", "value": "2020"}
  ]
}
```

## Development

### Adding New Features

1. Add source code to `src/marktplaats_backend/`
2. Add tests to `tests/`
3. Update imports in `src/marktplaats_backend/__init__.py`
4. Run tests: `python -m pytest tests/`

### Debugging

- Check CloudWatch logs for Lambda execution details
- Use `print()` statements in Lambda for debugging
- Test locally with `serverless invoke local`

## License

MIT License