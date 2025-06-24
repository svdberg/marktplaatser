# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a serverless AWS Lambda application for generating marketplace listings from images. The system processes uploaded images through AWS Rekognition for object detection and text extraction, then uses AWS Bedrock to generate structured listing data.

**Core Components:**
- `generate_listing_lambda.py` - Main Lambda handler that orchestrates the image processing pipeline
- `place_listing_lambda.py` - Posts the generated listing to the Marktplaats API
- `rekognition_utils.py` - AWS Rekognition integration for image analysis (label detection and text extraction)
- The serverless configuration references a `handler.py` module that is not present.

**Data Flow:**
1. Lambda receives base64-encoded image via HTTP POST
2. Image is uploaded to S3 bucket
3. Rekognition analyzes image for labels and text
4. Bedrock generates listing title, description, category, and attributes
5. Structured JSON response returned to client

## Deployment & Infrastructure

The application uses Serverless Framework for deployment configuration (`serverless.yaml`):
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
export MARKTPLAATS_CLIENT_ID=your_client_id
export MARKTPLAATS_CLIENT_SECRET=your_client_secret
cd marktplaats-backend
./deploy.sh
```
This script creates the S3 bucket if needed, deploys the stack and writes the
API endpoint to `endpoint.txt`.

**Test the deployed function:**
```bash
cd marktplaats-backend
./test.sh
```

**Local testing:**
```bash
cd marktplaats-backend
serverless invoke local -f generateListing
```

## Missing Implementation Files

The following utility modules are imported but not present in the codebase:
- `handler.py` - Expected by serverless.yaml but main handler is in `generate_listing_lambda.py`

## Configuration

Update the S3 bucket name in both:
- `generate_listing_lambda.py:9` (`s3_bucket` variable)
- `serverless.yaml:10` (`S3_BUCKET` environment variable)

Set your Marktplaats API credentials via the `MARKTPLAATS_CLIENT_ID` and
`MARKTPLAATS_CLIENT_SECRET` environment variables so that the lambdas can
authenticate to the API.

