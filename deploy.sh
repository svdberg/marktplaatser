#!/bin/bash

# Marktplaats AI Assistant - Full Deployment Script
# Deploys both backend (AWS Lambda) and frontend (S3) with proper error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="marktplaats-backend"
FRONTEND_DIR="marktplaats-frontend"
S3_BUCKET="marktplaats-frontend-simple-prod-website"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if required commands exist
    for cmd in aws serverless npm python pip; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check if directories exist
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory '$BACKEND_DIR' not found"
        exit 1
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory '$FRONTEND_DIR' not found"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check required environment variables
    if [ -z "$MARKTPLAATS_CLIENT_ID" ] || [ -z "$MARKTPLAATS_CLIENT_SECRET" ]; then
        log_error "Required environment variables not set:"
        log_error "  export MARKTPLAATS_CLIENT_ID=your_client_id"
        log_error "  export MARKTPLAATS_CLIENT_SECRET=your_client_secret"
        exit 1
    fi
    
    log_success "All requirements satisfied"
}

deploy_backend() {
    log_info "Deploying backend (AWS Lambda)..."
    
    cd "$BACKEND_DIR"
    
    # Check if serverless.yaml exists
    if [ ! -f "serverless.yaml" ]; then
        log_error "serverless.yaml not found in $BACKEND_DIR"
        exit 1
    fi
    
    # Install Python dependencies if needed
    if [ ! -d "venv" ] && [ ! -f ".requirements_installed" ]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
        touch .requirements_installed
    fi
    
    # Deploy with Serverless
    log_info "Running serverless deploy..."
    if serverless deploy; then
        log_success "Backend deployed successfully"
        
        # Get API Gateway URL
        if [ -f "endpoint.txt" ]; then
            BACKEND_URL=$(cat endpoint.txt)
            log_info "Backend URL: $BACKEND_URL"
        fi
    else
        log_error "Backend deployment failed"
        exit 1
    fi
    
    cd ..
}

deploy_frontend() {
    log_info "Deploying frontend (S3 + CloudFront)..."
    
    cd "$FRONTEND_DIR"
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        log_error "package.json not found in $FRONTEND_DIR"
        exit 1
    fi
    
    # Install Node.js dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing Node.js dependencies..."
        npm install
    fi
    
    # Build the frontend
    log_info "Building frontend..."
    if npm run generate; then
        log_success "Frontend build completed"
    else
        log_error "Frontend build failed"
        exit 1
    fi
    
    # Deploy to S3
    log_info "Deploying to S3 bucket: $S3_BUCKET"
    if aws s3 sync .output/public/ s3://$S3_BUCKET --delete; then
        log_success "Frontend deployed to S3"
        log_info "Frontend URL: http://$S3_BUCKET.s3-website.eu-west-1.amazonaws.com"
    else
        log_error "Frontend deployment to S3 failed"
        exit 1
    fi
    
    cd ..
}

run_post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    # Test backend endpoints
    if [ -n "$BACKEND_URL" ]; then
        log_info "Testing backend health..."
        if curl -f -s "$BACKEND_URL/categories" > /dev/null; then
            log_success "Backend is responding"
        else
            log_warning "Backend health check failed - this might be normal if CORS is configured"
        fi
    fi
    
    # Test frontend
    FRONTEND_URL="http://$S3_BUCKET.s3-website.eu-west-1.amazonaws.com"
    log_info "Testing frontend..."
    if curl -f -s "$FRONTEND_URL" > /dev/null; then
        log_success "Frontend is accessible"
    else
        log_warning "Frontend health check failed"
    fi
}

print_deployment_summary() {
    log_info "=== Deployment Summary ==="
    echo
    echo "🚀 Backend (AWS Lambda):"
    if [ -n "$BACKEND_URL" ]; then
        echo "   API URL: $BACKEND_URL"
    else
        echo "   API URL: Check marktplaats-backend/endpoint.txt"
    fi
    echo
    echo "🌐 Frontend (S3):"
    echo "   Website: http://$S3_BUCKET.s3-website.eu-west-1.amazonaws.com"
    echo
    echo "📋 Next Steps:"
    echo "   1. Test the application in your browser"
    echo "   2. Authorize with Marktplaats OAuth"
    echo "   3. Upload an image to test AI generation"
    echo
    echo "🔧 Useful Commands:"
    echo "   npm run logs:generate    # View backend logs"
    echo "   npm run deploy:backend   # Deploy backend only"
    echo "   npm run deploy:frontend  # Deploy frontend only"
    echo
}

# Main deployment flow
main() {
    echo
    log_info "🤖 Marktplaats AI Assistant - Full Deployment"
    echo "============================================="
    echo
    
    # Parse command line arguments
    BACKEND_ONLY=false
    FRONTEND_ONLY=false
    SKIP_TESTS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                BACKEND_ONLY=true
                shift
                ;;
            --frontend-only)
                FRONTEND_ONLY=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --backend-only    Deploy only the backend"
                echo "  --frontend-only   Deploy only the frontend"
                echo "  --skip-tests      Skip post-deployment tests"
                echo "  -h, --help        Show this help message"
                echo
                exit 0
                ;;
            *)
                log_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Check requirements
    check_requirements
    
    # Deploy based on options
    if [ "$FRONTEND_ONLY" = true ]; then
        deploy_frontend
    elif [ "$BACKEND_ONLY" = true ]; then
        deploy_backend
    else
        # Deploy both
        deploy_backend
        deploy_frontend
    fi
    
    # Run tests unless skipped
    if [ "$SKIP_TESTS" = false ]; then
        run_post_deployment_tests
    fi
    
    # Print summary
    print_deployment_summary
    
    log_success "🎉 Deployment completed successfully!"
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"