# Pinecone RAG Migration Guide

## Overview

This guide covers the migration from AWS OpenSearch/Bedrock Knowledge Base to Pinecone for cost optimization while maintaining the same RAG functionality.

## Cost Comparison

| Service | Current (AWS) | New (Pinecone) | Savings |
|---------|---------------|----------------|---------|
| Vector Database | OpenSearch Serverless (~$100+/month) | Pinecone Free Tier ($0/month) | ~$100+/month |
| Embeddings | AWS Bedrock (~$0.01/1000 requests) | AWS Bedrock (~$0.01/1000 requests) | No change |
| **Total** | **~$100+/month** | **~$0/month** | **~$100+/month** |

## Migration Steps

### 1. Prerequisites

```bash
# Set your Pinecone API key
export PINECONE_API_KEY='your_pinecone_api_key_here'
export PINECONE_ENVIRONMENT='us-east-1'  # or your preferred region
```

### 2. Setup Pinecone Index

```bash
# Create Pinecone index
python setup_pinecone.py
```

This will:
- Create a new index named "marktplaats-taxonomy"
- Configure 1536 dimensions (AWS Titan Text Embeddings v2)
- Set up cosine similarity metric
- Test basic connectivity

### 3. Upload Taxonomy Data

```bash
# Upload all taxonomy documents to Pinecone
python upload_to_pinecone.py
```

This will:
- Load all KB documents from `kb_documents/`
- Generate embeddings using AWS Titan Text Embeddings v2
- Upload vectors to Pinecone in batches
- Test search functionality

### 4. Update Lambda Function

The migration includes a new `pinecone_rag_utils.py` module that provides:

- **Backward compatibility**: Same function signatures
- **Improved performance**: Direct vector search vs. Knowledge Base API
- **Cost optimization**: No OpenSearch charges

### 5. Test the Migration

```bash
# Test the complete migration
python test_pinecone_migration.py
```

## Architecture Changes

### Before (AWS OpenSearch)
```
Image → Claude Vision → Bedrock Knowledge Base (OpenSearch) → RetrieveAndGenerate → Result
```

### After (Pinecone)
```
Image → Claude Vision → Pinecone Vector Search → Claude Attribute Generation → Result
```

## Key Benefits

1. **Cost Reduction**: ~$100+/month savings
2. **Performance**: Direct vector search is faster than Knowledge Base API
3. **Flexibility**: Full control over vector search parameters
4. **Scalability**: Pinecone free tier supports 1M vectors

## Environment Variables

Add to your deployment configuration:

```bash
export PINECONE_API_KEY='your_api_key'
export PINECONE_ENVIRONMENT='us-east-1'
```

## Deployment

### Lambda Function Updates

The migration requires updating the Lambda function to use the new Pinecone RAG utilities:

```python
# OLD: AWS Bedrock Knowledge Base
from marktplaats_backend.bedrock_rag_utils import generate_listing_with_knowledge_base

# NEW: Pinecone RAG (backward compatible)
from marktplaats_backend.pinecone_rag_utils import generate_listing_with_knowledge_base
```

### Serverless Configuration

Update `serverless.yaml`:

```yaml
environment:
  PINECONE_API_KEY: ${env:PINECONE_API_KEY}
  PINECONE_ENVIRONMENT: ${env:PINECONE_ENVIRONMENT, 'us-east-1'}
```

## Monitoring

### Performance Metrics
- Target response time: <25s (API Gateway limit)
- Expected response time: ~10-15s
- Success rate: >95%

### Cost Monitoring
- Pinecone: Free tier (1M vectors, 1 index)
- AWS Bedrock: Only embedding generation (~$0.01/1000 requests)
- Total cost reduction: ~$100+/month

## Rollback Plan

If issues occur, you can quickly rollback:

1. **Code rollback**: Use git to revert to previous version
2. **Keep OpenSearch**: Don't delete the Knowledge Base immediately
3. **Environment variables**: Remove Pinecone environment variables

## Testing Checklist

- [ ] Pinecone index created successfully
- [ ] Taxonomy data uploaded (1,943 categories)
- [ ] Category search works for test queries
- [ ] Full RAG pipeline generates valid listings
- [ ] Performance meets <25s requirement
- [ ] Cost monitoring shows $0 Pinecone charges

## Support

For issues:
1. Check Pinecone console for index status
2. Verify API key permissions
3. Monitor AWS CloudWatch logs
4. Test with `test_pinecone_migration.py`

## Next Steps

1. **Deploy to staging**: Test in staging environment
2. **Monitor performance**: Track response times and success rates
3. **Optimize queries**: Fine-tune search parameters if needed
4. **Cleanup**: Remove AWS Knowledge Base after successful migration