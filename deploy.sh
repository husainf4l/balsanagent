#!/bin/bash

# AI Business Advisor - Complete Deployment Script
# Supports both development and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-business-advisor"
FASTAPI_PORT=8000
NESTJS_PORT=3001
NEXTJS_PORT=3000

echo -e "${BLUE}🚀 AI Business Advisor Deployment Script${NC}"
echo "============================================"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${BLUE}Checking Prerequisites...${NC}"
    
    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        print_status "Node.js $NODE_VERSION found"
    else
        print_error "Node.js not found. Please install Node.js 18+"
        exit 1
    fi
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        print_status "npm $NPM_VERSION found"
    else
        print_error "npm not found"
        exit 1
    fi
    
    # Check pip
    if command_exists pip3; then
        print_status "pip3 found"
    else
        print_error "pip3 not found"
        exit 1
    fi
    
    # Optional: Check Docker
    if command_exists docker; then
        print_status "Docker found (optional)"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found (optional for containerized deployment)"
        DOCKER_AVAILABLE=false
    fi
    
    # Optional: Check PM2
    if command_exists pm2; then
        print_status "PM2 found (optional)"
        PM2_AVAILABLE=true
    else
        print_warning "PM2 not found (optional for process management)"
        PM2_AVAILABLE=false
    fi
}

# Function to create directories
create_directories() {
    echo -e "\n${BLUE}Creating Project Structure...${NC}"
    
    # Create logs directory
    mkdir -p logs
    print_status "Created logs directory"
    
    # Create data directory
    mkdir -p data
    print_status "Created data directory"
    
    # Create monitoring directories
    mkdir -p monitoring/grafana/dashboards
    print_status "Created monitoring directories"
}

# Function to setup FastAPI
setup_fastapi() {
    echo -e "\n${BLUE}Setting up FastAPI...${NC}"
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip3 install -r requirements.txt
        print_status "FastAPI dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Check if main_streaming.py exists
    if [ -f "main_streaming.py" ]; then
        print_status "FastAPI streaming server ready"
    else
        print_error "main_streaming.py not found"
        exit 1
    fi
}

# Function to setup NestJS
setup_nestjs() {
    echo -e "\n${BLUE}Setting up NestJS Backend...${NC}"
    
    if [ ! -d "ai-chat-backend" ]; then
        print_status "Creating NestJS project..."
        
        # Check if NestJS CLI is installed
        if ! command_exists nest; then
            print_status "Installing NestJS CLI..."
            npm install -g @nestjs/cli
        fi
        
        # Create NestJS project
        nest new ai-chat-backend --package-manager npm --skip-git
        
        cd ai-chat-backend
        
        # Install additional dependencies
        npm install @nestjs/config @nestjs/throttler axios class-validator class-transformer
        npm install --save-dev @types/node
        
        print_status "NestJS project created"
        cd ..
    else
        print_status "NestJS project already exists"
        cd ai-chat-backend
        npm install
        cd ..
    fi
}

# Function to setup Next.js
setup_nextjs() {
    echo -e "\n${BLUE}Setting up Next.js Frontend...${NC}"
    
    if [ ! -d "ai-chat-frontend" ]; then
        print_status "Creating Next.js project..."
        npx create-next-app@latest ai-chat-frontend --typescript --tailwind --app --src-dir --import-alias="@/*" --skip-git
        
        cd ai-chat-frontend
        npm install
        print_status "Next.js project created"
        cd ..
    else
        print_status "Next.js project already exists"
        cd ai-chat-frontend
        npm install
        cd ..
    fi
}

# Function to create environment files
create_env_files() {
    echo -e "\n${BLUE}Creating Environment Files...${NC}"
    
    # FastAPI .env
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# FastAPI Configuration
ENVIRONMENT=development
STREAMING_ENABLED=true
STREAMING_DELAY=0.1
MAX_CONCURRENT_STREAMS=50
LOG_LEVEL=info

# OpenAI Configuration (update with your keys)
OPENAI_API_KEY=your-openai-api-key

# Database Configuration (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/ai_chat
EOF
        print_status "Created FastAPI .env file"
    fi
    
    # NestJS .env
    if [ ! -f "ai-chat-backend/.env" ]; then
        cat > ai-chat-backend/.env << EOF
# NestJS Configuration
PORT=3001
NODE_ENV=development

# FastAPI Chat Agent
FASTAPI_BASE_URL=http://localhost:8000

# Rate Limiting
THROTTLE_TTL=60
THROTTLE_LIMIT=100

# Optional: Authentication
JWT_SECRET=your-jwt-secret-change-this-in-production
API_KEY=your-api-key
EOF
        print_status "Created NestJS .env file"
    fi
    
    # Next.js .env.local
    if [ ! -f "ai-chat-frontend/.env.local" ]; then
        cat > ai-chat-frontend/.env.local << EOF
# Next.js Configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
EOF
        print_status "Created Next.js .env.local file"
    fi
}

# Function to start services
start_services() {
    local mode=$1
    
    echo -e "\n${BLUE}Starting Services in $mode mode...${NC}"
    
    if [ "$mode" = "development" ]; then
        start_development_services
    elif [ "$mode" = "production" ]; then
        start_production_services
    fi
}

# Function to start development services
start_development_services() {
    echo -e "\n${YELLOW}Starting Development Services...${NC}"
    
    # Function to start service in background
    start_service() {
        local name=$1
        local command=$2
        local port=$3
        local log_file=$4
        
        echo "Starting $name on port $port..."
        eval "$command" > "logs/$log_file" 2>&1 &
        local pid=$!
        echo $pid > "logs/$name.pid"
        
        # Wait a bit and check if service started
        sleep 3
        if kill -0 $pid 2>/dev/null; then
            print_status "$name started (PID: $pid)"
        else
            print_error "$name failed to start"
            cat "logs/$log_file"
            return 1
        fi
    }
    
    # Start FastAPI
    start_service "fastapi" "python3 main_streaming.py" $FASTAPI_PORT "fastapi.log"
    
    # Start NestJS
    cd ai-chat-backend
    start_service "nestjs" "npm run start:dev" $NESTJS_PORT "nestjs.log"
    cd ..
    
    # Start Next.js
    cd ai-chat-frontend
    start_service "nextjs" "npm run dev" $NEXTJS_PORT "nextjs.log"
    cd ..
    
    echo -e "\n${GREEN}🎉 All services started successfully!${NC}"
    echo "======================================"
    echo "📱 Frontend: http://localhost:$NEXTJS_PORT"
    echo "🔧 NestJS API: http://localhost:$NESTJS_PORT"
    echo "🤖 FastAPI: http://localhost:$FASTAPI_PORT"
    echo ""
    echo "📋 Logs are in the logs/ directory"
    echo "🛑 To stop services: ./deploy.sh stop"
}

# Function to start production services
start_production_services() {
    echo -e "\n${YELLOW}Starting Production Services...${NC}"
    
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo "Using Docker Compose..."
        docker-compose up -d
        print_status "Docker services started"
    elif [ "$PM2_AVAILABLE" = true ]; then
        echo "Using PM2..."
        pm2 start ecosystem.config.js
        print_status "PM2 services started"
    else
        print_warning "No production process manager available"
        print_warning "Falling back to development mode"
        start_development_services
    fi
}

# Function to stop services
stop_services() {
    echo -e "\n${BLUE}Stopping Services...${NC}"
    
    # Stop services by PID
    for service in fastapi nestjs nextjs; do
        if [ -f "logs/$service.pid" ]; then
            local pid=$(cat "logs/$service.pid")
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                print_status "Stopped $service (PID: $pid)"
            fi
            rm -f "logs/$service.pid"
        fi
    done
    
    # Also try Docker and PM2 cleanup
    if [ "$DOCKER_AVAILABLE" = true ]; then
        docker-compose down 2>/dev/null || true
    fi
    
    if [ "$PM2_AVAILABLE" = true ]; then
        pm2 delete all 2>/dev/null || true
    fi
    
    print_status "All services stopped"
}

# Function to run tests
run_tests() {
    echo -e "\n${BLUE}Running Tests...${NC}"
    
    if [ -f "test_streaming.sh" ]; then
        chmod +x test_streaming.sh
        ./test_streaming.sh
    else
        print_warning "test_streaming.sh not found, skipping tests"
    fi
}

# Function to show status
show_status() {
    echo -e "\n${BLUE}Service Status...${NC}"
    
    # Check if services are running
    check_service_status() {
        local name=$1
        local port=$2
        
        if curl -s "http://localhost:$port" >/dev/null 2>&1 || curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
            print_status "$name is running on port $port"
        else
            print_error "$name is not running on port $port"
        fi
    }
    
    check_service_status "FastAPI" $FASTAPI_PORT
    check_service_status "NestJS" $NESTJS_PORT
    check_service_status "Next.js" $NEXTJS_PORT
    
    # Show Docker status
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo -e "\nDocker containers:"
        docker-compose ps 2>/dev/null || echo "No Docker containers running"
    fi
    
    # Show PM2 status
    if [ "$PM2_AVAILABLE" = true ]; then
        echo -e "\nPM2 processes:"
        pm2 list 2>/dev/null || echo "No PM2 processes running"
    fi
}

# Function to show help
show_help() {
    echo "AI Business Advisor Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup          Setup the complete project"
    echo "  dev            Start in development mode"
    echo "  prod           Start in production mode"
    echo "  stop           Stop all services"
    echo "  status         Show service status"
    echo "  test           Run tests"
    echo "  logs           Show recent logs"
    echo "  clean          Clean up logs and temporary files"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup       # First-time setup"
    echo "  $0 dev         # Start development server"
    echo "  $0 status      # Check if services are running"
}

# Function to show logs
show_logs() {
    echo -e "\n${BLUE}Recent Logs...${NC}"
    
    for service in fastapi nestjs nextjs; do
        if [ -f "logs/$service.log" ]; then
            echo -e "\n${YELLOW}=== $service logs ===${NC}"
            tail -20 "logs/$service.log"
        fi
    done
}

# Function to clean up
clean_up() {
    echo -e "\n${BLUE}Cleaning up...${NC}"
    
    # Stop services first
    stop_services
    
    # Clean logs
    rm -rf logs/*.log logs/*.pid
    
    # Clean Docker (optional)
    if [ "$DOCKER_AVAILABLE" = true ]; then
        docker-compose down --volumes --remove-orphans 2>/dev/null || true
    fi
    
    print_status "Cleanup completed"
}

# Main script logic
main() {
    case "${1:-help}" in
        "setup")
            check_prerequisites
            create_directories
            setup_fastapi
            setup_nestjs
            setup_nextjs
            create_env_files
            print_status "Setup completed successfully!"
            echo ""
            echo "Next steps:"
            echo "1. Update .env files with your API keys"
            echo "2. Copy NestJS and Next.js implementation files from README"
            echo "3. Run: $0 dev"
            ;;
        "dev"|"development")
            check_prerequisites
            start_services "development"
            ;;
        "prod"|"production")
            check_prerequisites
            start_services "production"
            ;;
        "stop")
            stop_services
            ;;
        "status")
            show_status
            ;;
        "test")
            run_tests
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            clean_up
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
