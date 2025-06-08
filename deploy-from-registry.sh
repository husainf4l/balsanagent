#!/bin/bash

# Remote Deployment Script - Deploy from Docker Registry
# Run this script on your server - no source code needed!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE VALUES
DOCKER_REGISTRY="your-dockerhub-username"  # Your Docker Hub username
IMAGE_NAME="ai-advisor-api"
VERSION="latest"
FULL_IMAGE_NAME="$DOCKER_REGISTRY/$IMAGE_NAME:$VERSION"
CONTAINER_NAME="ai-advisor-api"
PORT="8000"

echo -e "${BLUE}🚀 Deploying AI Advisor API from Docker Registry${NC}"
echo "===================================================="

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

# Get environment variables
echo -e "${BLUE}🔧 Setting up environment...${NC}"
read -p "Enter your DATABASE_URL: " DATABASE_URL
read -s -p "Enter your OPENAI_API_KEY: " OPENAI_API_KEY
echo ""

if [ -z "$DATABASE_URL" ] || [ -z "$OPENAI_API_KEY" ]; then
    print_error "DATABASE_URL and OPENAI_API_KEY are required!"
    exit 1
fi

# Stop and remove existing container if it exists
echo -e "${BLUE}🛑 Stopping existing container (if any)...${NC}"
docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
print_status "Cleaned up existing container"

# Pull the latest image
echo -e "${BLUE}📥 Pulling latest image from registry...${NC}"
docker pull $FULL_IMAGE_NAME
print_status "Image pulled successfully"

# Run the container
echo -e "${BLUE}🚀 Starting AI Advisor API container...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e ENVIRONMENT=production \
  -e STREAMING_ENABLED=true \
  -e STREAMING_DELAY=0.05 \
  -e MAX_CONCURRENT_STREAMS=100 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  $FULL_IMAGE_NAME

print_status "Container started successfully"

# Wait for service to be healthy
echo -e "${BLUE}⏳ Waiting for service to be healthy...${NC}"
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        print_status "Service is healthy!"
        break
    fi
    
    if [ $counter -eq $((timeout-1)) ]; then
        print_error "Service failed to become healthy within $timeout seconds"
        echo "Check logs with: docker logs $CONTAINER_NAME"
        exit 1
    fi
    
    echo -n "."
    sleep 1
    counter=$((counter + 1))
done

# Test the API
echo -e "${BLUE}🧪 Testing API endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:$PORT/health)
print_status "API is responding"
echo -e "${GREEN}Health check response:${NC} $HEALTH_RESPONSE"

# Show container status
echo -e "${BLUE}📋 Container status:${NC}"
docker ps | grep $CONTAINER_NAME

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Your FastAPI backend is now running on:"
echo "  • http://localhost:$PORT"
echo "  • Your NestJS can access it at: http://localhost:$PORT"
echo ""
echo "Useful commands:"
echo "  • View logs: docker logs -f $CONTAINER_NAME"
echo "  • Stop service: docker stop $CONTAINER_NAME"
echo "  • Restart service: docker restart $CONTAINER_NAME"
echo "  • Remove service: docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo ""
echo "To update to a new version:"
echo "  1. docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo "  2. docker pull $FULL_IMAGE_NAME"
echo "  3. Run this script again"
