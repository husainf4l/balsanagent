#!/bin/bash

# Build and Push to Docker Registry Script
# This allows deployment without copying files to server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY="your-dockerhub-username"  # Change this to your Docker Hub username
IMAGE_NAME="ai-advisor-api"
VERSION="latest"
FULL_IMAGE_NAME="$DOCKER_REGISTRY/$IMAGE_NAME:$VERSION"

echo -e "${BLUE}🚀 Building and Pushing AI Advisor API to Docker Registry${NC}"
echo "================================================================"

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
print_status "Docker is running"

# Build the image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -f Dockerfile.fastapi -t $FULL_IMAGE_NAME .
print_status "Image built successfully: $FULL_IMAGE_NAME"

# Test the image locally (optional)
echo -e "${BLUE}🧪 Testing image locally...${NC}"
CONTAINER_ID=$(docker run -d -p 8001:8000 $FULL_IMAGE_NAME)
sleep 10

if curl -s http://localhost:8001/health > /dev/null; then
    print_status "Local test passed"
    docker stop $CONTAINER_ID > /dev/null
    docker rm $CONTAINER_ID > /dev/null
else
    print_warning "Local test failed, but proceeding with push"
    docker stop $CONTAINER_ID > /dev/null 2>&1 || true
    docker rm $CONTAINER_ID > /dev/null 2>&1 || true
fi

# Login to Docker Hub (you'll be prompted for credentials)
echo -e "${BLUE}🔐 Logging into Docker Hub...${NC}"
docker login

# Push the image
echo -e "${BLUE}📤 Pushing image to Docker Hub...${NC}"
docker push $FULL_IMAGE_NAME
print_status "Image pushed successfully to Docker Hub"

# Clean up local test image
docker rmi $FULL_IMAGE_NAME > /dev/null 2>&1 || true

echo -e "${GREEN}🎉 Build and push complete!${NC}"
echo ""
echo "Your image is now available at: $FULL_IMAGE_NAME"
echo ""
echo "To deploy on your server, run:"
echo "docker run -d -p 8000:8000 --name ai-advisor-api \\"
echo "  -e DATABASE_URL='your_database_url' \\"
echo "  -e OPENAI_API_KEY='your_openai_key' \\"
echo "  $FULL_IMAGE_NAME"
echo ""
echo "Or use the server deployment script with this image."
