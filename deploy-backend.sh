#!/bin/bash

# AI Business Advisor FastAPI Backend Deployment Script
# For deploying alongside existing NestJS application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="ai-advisor-api"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"

echo -e "${BLUE}🚀 Deploying AI Advisor FastAPI Backend${NC}"
echo "=========================================="

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

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    print_warning "Environment file $ENV_FILE not found. Creating template..."
    cat > "$ENV_FILE" << EOF
# Production Environment Variables for AI Advisor FastAPI
DATABASE_URL=postgresql://username:password@host:5432/database
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo -e "${YELLOW}Please edit $ENV_FILE with your actual values before continuing.${NC}"
    echo "Press Enter when ready to continue..."
    read
fi

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | xargs)
print_status "Environment variables loaded"

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f "$COMPOSE_FILE" down || true
print_status "Existing containers stopped"

# Build and start the service
echo -e "${BLUE}🔨 Building and starting AI Advisor API...${NC}"
docker-compose -f "$COMPOSE_FILE" up --build -d

# Wait for service to be healthy
echo -e "${BLUE}⏳ Waiting for service to be healthy...${NC}"
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
        print_status "Service is healthy!"
        break
    fi
    
    if [ $counter -eq $((timeout-1)) ]; then
        print_error "Service failed to become healthy within $timeout seconds"
        echo "Check logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi
    
    echo -n "."
    sleep 1
    counter=$((counter + 1))
done

# Test the API
echo -e "${BLUE}🧪 Testing API endpoint...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    print_status "API is responding on port 8000"
    echo -e "${GREEN}Health check response:${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool || echo "Response received"
else
    print_warning "API health check failed, but container might still be starting"
fi

# Show running containers
echo -e "${BLUE}📋 Current container status:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Show logs
echo -e "${BLUE}📄 Recent logs:${NC}"
docker-compose -f "$COMPOSE_FILE" logs --tail=20

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Your FastAPI backend is now running on:"
echo "  • Local: http://localhost:8000"
echo "  • Your NestJS can access it at: http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  • View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  • Stop service: docker-compose -f $COMPOSE_FILE down"
echo "  • Restart service: docker-compose -f $COMPOSE_FILE restart"
echo "  • Check status: docker-compose -f $COMPOSE_FILE ps"
echo ""
echo -e "${YELLOW}Make sure to update your NestJS configuration to use:${NC}"
echo -e "${YELLOW}FASTAPI_URL=http://localhost:8000${NC}"
