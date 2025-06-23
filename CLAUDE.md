# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a serverless AWS Lambda application for generating marketplace listings from images. The system processes uploaded images through AWS Rekognition for object detection and text extraction, then uses AWS Bedrock to generate structured listing data.

**Core Components:**
- `generate_listing_lambda.py` - Main Lambda handler that orchestrates the image processing pipeline
- `rekognition_utils.py` - AWS Rekognition integration for image analysis (label detection and text extraction)
- Missing utility modules referenced in imports: `bedrock_utils.py`, `s3_utils.py`, `handler.py`

**Data Flow:**
1. Lambda receives base64-encoded image via HTTP POST
2. Image is uploaded to S3 bucket
3. Rekognition analyzes image for labels and text
4. Bedrock generates listing title, description, category, and attributes
5. Structured JSON response returned to client

## Deployment & Infrastructure

The application uses Serverless Framework for deployment configuration (`serverless_backend.yaml`):
- Runtime: Python 3.11
- Region: eu-west-1
- Memory: 512MB
- Timeout: 30s
- HTTP endpoint: POST `/generate-listing`

**Required AWS permissions:**
- Rekognition: DetectLabels, DetectText
- S3: PutObject, GetObject
- Bedrock: InvokeModel

## Development Commands

**Install dependencies:**
```bash
pip install -r marktplaats-backend/requirements.txt
```

**Deploy to AWS:**
```bash
cd marktplaats-backend
serverless deploy
```

**Local testing:**
```bash
cd marktplaats-backend
serverless invoke local -f generateListing
```

## Missing Implementation Files

The following utility modules are imported but not present in the codebase:
- `bedrock_utils.py` - Should contain `generate_listing_with_bedrock()` function
- `s3_utils.py` - Should contain `upload_image_to_s3()` function
- `handler.py` - Expected by serverless.yaml but main handler is in `generate_listing_lambda.py`

## Configuration

Update the S3 bucket name in both:
- `generate_listing_lambda.py:9` (`s3_bucket` variable)
- `serverless_backend.yaml:10` (`S3_BUCKET` environment variable)