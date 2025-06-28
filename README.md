# 🤖 Marktplaats AI Assistant

An AI-powered application that automatically generates Marktplaats listings from product images. Uses AWS Rekognition for image analysis, Claude Sonnet for intelligent content generation, and includes smart price estimation based on the Dutch second-hand market.

## ✨ Features

- **📸 Image Analysis**: Upload product photos and get automatic object detection
- **🧠 AI-Generated Listings**: Claude Sonnet creates titles, descriptions, and categories
- **💰 Smart Price Estimation**: AI suggests realistic prices for the Dutch market
- **🔐 OAuth Integration**: Secure Marktplaats account authorization
- **📱 Mobile Optimized**: Automatic image compression for mobile devices
- **📋 Full CRUD**: Create, read, update, and delete advertisements
- **🖼️ Image Management**: Upload and display advertisement images

## 🏗️ Architecture

### Backend (AWS Lambda + Serverless)
- **Runtime**: Python 3.11
- **Framework**: Serverless Framework
- **Services**: AWS Lambda, API Gateway, S3, DynamoDB, Rekognition, Bedrock
- **AI Model**: Claude Sonnet 3.7 via AWS Bedrock

### Frontend (Nuxt.js + Vue 3)
- **Framework**: Nuxt.js 3 with Vue 3 Composition API
- **Styling**: Tailwind CSS with custom components
- **Deployment**: Static site on AWS S3
- **Features**: PWA ready with offline support

### External APIs
- **Marktplaats API**: OAuth, category management, advertisement CRUD
- **AWS Rekognition**: Image analysis and text extraction
- **AWS Bedrock**: Claude Sonnet for content generation

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- AWS CLI configured with appropriate permissions
- Serverless Framework (`npm install -g serverless`)
- Marktplaats API credentials (client ID and secret)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd marktplaatser

# Install dependencies
npm run install:all
```

### 2. Environment Configuration

#### Backend Environment
```bash
# Required environment variables
export MARKTPLAATS_CLIENT_ID=your_client_id
export MARKTPLAATS_CLIENT_SECRET=your_client_secret

# Optional for local development
export IS_LOCAL=true
```

#### Frontend Configuration
Update `marktplaats-frontend/.env.production`:
```
NUXT_PUBLIC_API_BASE_URL=your_api_gateway_url
```

### 3. Deploy Everything

```bash
# Deploy both backend and frontend
./deploy.sh

# Or deploy individually
npm run deploy:backend
npm run deploy:frontend
```

## 📁 Project Structure

```
marktplaatser/
├── README.md                          # This file
├── deploy.sh                          # Root deployment script
├── package.json                       # Root package.json with scripts
│
├── marktplaats-backend/               # AWS Lambda backend
│   ├── src/marktplaats_backend/       # Python source code
│   │   ├── generate_listing_lambda.py # Main listing generation
│   │   ├── bedrock_utils.py           # Claude Sonnet integration
│   │   ├── rekognition_utils.py       # AWS Rekognition utilities
│   │   ├── marktplaats_auth.py        # OAuth and token management
│   │   ├── marktplaats_ads_api.py     # Marktplaats API integration
│   │   ├── category_matcher.py        # Category matching logic
│   │   └── attribute_mapper.py        # Attribute mapping utilities
│   ├── tests/                         # Unit and integration tests
│   ├── serverless.yaml               # Serverless configuration
│   ├── requirements.txt              # Python dependencies
│   └── deploy.sh                     # Backend deployment script
│
└── marktplaats-frontend/             # Nuxt.js frontend
    ├── pages/                        # Vue.js pages
    │   ├── index.vue                 # Main image upload and listing generation
    │   ├── listings.vue              # Advertisement management
    │   └── callback.vue              # OAuth callback handler
    ├── components/                   # Reusable Vue components
    │   ├── EditListingModal.vue      # Advertisement editing modal
    │   └── CategorySelector.vue      # Category selection component
    ├── nuxt.config.ts               # Nuxt configuration
    ├── serverless.yml              # Frontend deployment config
    └── deploy.sh                   # Frontend deployment script
```

## 🔧 Development

### Backend Development

```bash
cd marktplaats-backend

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Code quality
flake8 src/ tests/
black src/ tests/
mypy src/

# Local testing
serverless invoke local -f generateListing

# Deploy single function
serverless deploy function -f generateListing
```

### Frontend Development

```bash
cd marktplaats-frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run generate

# Deploy to S3
./deploy.sh
```

### Key Development Files

#### Backend Core Functions
- `generate_listing_lambda.py` - Main entry point for image analysis and listing generation
- `bedrock_utils.py` - Claude Sonnet integration with vision capabilities and price estimation
- `marktplaats_ads_api.py` - Complete Marktplaats API wrapper with CRUD operations
- `manage_advertisement_lambda.py` - Advertisement management endpoints

#### Frontend Core Pages
- `pages/index.vue` - Main application with image upload and AI generation
- `pages/listings.vue` - Advertisement management with edit/delete functionality
- `components/EditListingModal.vue` - Modal for editing advertisements

## 🔑 API Endpoints

### Backend Endpoints (API Gateway)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate-listing` | Generate listing from image |
| POST | `/create-advertisement` | Create advertisement on Marktplaats |
| GET | `/oauth/authorize` | Start OAuth flow |
| GET | `/oauth/callback` | Handle OAuth callback |
| GET | `/categories` | Get Marktplaats categories |
| GET | `/list-advertisements` | List user advertisements |
| GET | `/advertisement-images/{id}` | Get advertisement images |
| GET | `/manage-advertisement/{id}` | Get advertisement details |
| PATCH | `/manage-advertisement/{id}` | Update advertisement |
| DELETE | `/manage-advertisement/{id}` | Delete advertisement |

### Request/Response Examples

#### Generate Listing
```bash
curl -X POST https://your-api.com/dev/generate-listing \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image_data"}'
```

Response:
```json
{
  "title": "Vintage houten tafel - eiken",
  "description": "Mooie vintage eiken tafel...",
  "categoryId": 621,
  "categoryName": "Tafels > Eettafels",
  "attributes": [...],
  "estimatedPrice": 150,
  "priceRange": {"min": 120, "max": 180},
  "priceConfidence": "hoog"
}
```

## 🛠️ Configuration

### AWS Services Setup

#### Required AWS Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "s3:*",
        "dynamodb:*",
        "rekognition:DetectLabels",
        "rekognition:DetectText",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

#### DynamoDB Table
The `marktplaats-user-tokens` table is automatically created by Serverless Framework.

#### S3 Buckets
- `marktplaatser-images` - Image storage (auto-created)
- `marktplaats-frontend-simple-prod-website` - Frontend hosting

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MARKTPLAATS_CLIENT_ID` | Marktplaats API client ID | Yes |
| `MARKTPLAATS_CLIENT_SECRET` | Marktplaats API client secret | Yes |
| `AWS_REGION` | AWS region (default: eu-west-1) | No |
| `IS_LOCAL` | Enable local development mode | No |

## 🧪 Testing

### Backend Tests
```bash
cd marktplaats-backend

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python tests/test_integration.py  # Integration tests
python tests/test_attribute_mapping.py  # Unit tests

# Test deployed function
./test.sh sample.jpg
```

### Frontend Testing
```bash
cd marktplaats-frontend

# Build test
npm run generate

# Manual testing
npm run dev  # Test at http://localhost:3000
```

## 📱 Mobile Optimization

The application includes several mobile-specific optimizations:

- **Image Compression**: Automatic resizing to 1024x1024 with 80% quality
- **Progress Feedback**: Loading states for compression and AI processing
- **Responsive Design**: Tailwind CSS with mobile-first approach
- **Touch-Friendly**: Large buttons and intuitive gestures

## 🔒 Security

- **OAuth 2.0**: Secure Marktplaats account integration
- **Token Storage**: Encrypted user tokens in DynamoDB
- **CORS Protection**: Configured for specific frontend domains
- **Input Validation**: Client and server-side validation
- **API Rate Limiting**: Handled by AWS API Gateway

## 🚦 Deployment

### Production Deployment

```bash
# Full deployment
./deploy.sh

# Backend only
cd marktplaats-backend && ./deploy.sh

# Frontend only
cd marktplaats-frontend && ./deploy.sh
```

### Deployment Checklist

- [ ] AWS credentials configured
- [ ] Marktplaats API credentials set
- [ ] Environment variables configured
- [ ] Tests passing
- [ ] CORS domains updated for production

## 🐛 Troubleshooting

### Common Issues

#### "Image too large" errors on mobile
- **Solution**: Image compression is automatic, but very large images (>10MB) may still timeout
- **Workaround**: Use the 1024x1024 compression setting

#### OAuth callback errors
- **Solution**: Ensure callback URL matches Marktplaats app configuration
- **Check**: `FRONTEND_DOMAIN` environment variable

#### Category matching failures
- **Solution**: Categories are fetched from Marktplaats API in real-time
- **Check**: Internet connectivity and API credentials

#### Price estimation not working
- **Solution**: Ensure AWS Bedrock has access to Claude Sonnet 3.7
- **Check**: AWS region (must be eu-west-1) and model permissions

### Logging and Debugging

#### Backend Logs
```bash
# CloudWatch logs
aws logs tail /aws/lambda/marktplaats-backend-dev-generateListing --follow

# Specific function
serverless logs -f generateListing -t
```

#### Frontend Debugging
- Open browser developer tools
- Check console for compression logs
- Network tab for API call failures

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**: Fork the repository and clone locally
2. **Feature Branch**: Create a feature branch (`git checkout -b feature/amazing-feature`)
3. **Development**: Make changes and test thoroughly
4. **Tests**: Ensure all tests pass
5. **Documentation**: Update README if needed
6. **Pull Request**: Submit PR with clear description

### Code Style

#### Backend (Python)
- **Formatter**: Black
- **Linter**: Flake8
- **Type Checking**: MyPy
- **Docstrings**: Google style

#### Frontend (Vue/TypeScript)
- **Formatter**: Prettier
- **Linter**: ESLint
- **Style**: Vue 3 Composition API
- **CSS**: Tailwind CSS classes

## 📚 Additional Resources

- [Marktplaats API Documentation](https://api.marktplaats.nl/docs/)
- [AWS Bedrock Claude Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
- [Nuxt.js Documentation](https://nuxt.com/docs)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions, issues, or contributions:

1. **Check Issues**: Look for existing GitHub issues
2. **Create Issue**: Describe your problem with steps to reproduce
3. **Discussion**: Use GitHub Discussions for questions

---

**Made with ❤️ and 🤖 AI assistance**