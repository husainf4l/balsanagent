#!/bin/bash

# Health Check Script for AI Business Advisor
# Comprehensive health monitoring for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FASTAPI_URL="http://localhost:8000"
NESTJS_URL="http://localhost:3001"
NEXTJS_URL="http://localhost:3000"
TIMEOUT=10

echo -e "${BLUE}🏥 AI Business Advisor Health Check${NC}"
echo "====================================="

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    # Use curl with timeout and follow redirects
    local response=$(curl -s -w "%{http_code}" -m $TIMEOUT "$url" -o /dev/null 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ Healthy (HTTP $response)${NC}"
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ Connection failed${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠ Unexpected status (HTTP $response)${NC}"
        return 1
    fi
}

# Function to check streaming endpoint
check_streaming() {
    local name=$1
    local url=$2
    
    echo -n "Checking $name streaming... "
    
    # Test streaming with a simple message
    local response=$(timeout $TIMEOUT curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d '{"message": "Health check", "session_id": "health-check"}' \
        --no-buffer 2>/dev/null | head -3)
    
    if echo "$response" | grep -q "data:"; then
        echo -e "${GREEN}✓ Streaming works${NC}"
        return 0
    else
        echo -e "${RED}✗ Streaming failed${NC}"
        return 1
    fi
}

# Function to check API functionality
check_api_functionality() {
    echo -e "\n${BLUE}API Functionality Tests${NC}"
    echo "----------------------"
    
    # Test session creation
    echo -n "Testing session creation... "
    local session_response=$(curl -s -X POST "$NESTJS_URL/api/sessions" -m $TIMEOUT 2>/dev/null)
    
    if echo "$session_response" | grep -q "session_id"; then
        echo -e "${GREEN}✓ Sessions work${NC}"
        
        # Extract session ID for further testing
        local session_id=$(echo "$session_response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        
        # Test chat with session
        echo -n "Testing chat functionality... "
        local chat_response=$(curl -s -X POST "$NESTJS_URL/api/chat" \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"Hello\", \"session_id\": \"$session_id\"}" \
            -m $TIMEOUT 2>/dev/null)
        
        if echo "$chat_response" | grep -q "response"; then
            echo -e "${GREEN}✓ Chat works${NC}"
        else
            echo -e "${RED}✗ Chat failed${NC}"
        fi
    else
        echo -e "${RED}✗ Sessions failed${NC}"
    fi
}

# Function to check resource usage
check_resources() {
    echo -e "\n${BLUE}Resource Usage${NC}"
    echo "--------------"
    
    # Check memory usage
    if command -v ps >/dev/null 2>&1; then
        echo "Memory usage by service:"
        
        # FastAPI (Python processes)
        local python_mem=$(ps aux | grep python | grep -v grep | awk '{sum+=$4} END {printf "%.1f", sum}' 2>/dev/null || echo "0")
        echo -e "  FastAPI (Python): ${python_mem}% memory"
        
        # Node.js processes
        local node_mem=$(ps aux | grep node | grep -v grep | awk '{sum+=$4} END {printf "%.1f", sum}' 2>/dev/null || echo "0")
        echo -e "  Node.js (NestJS + Next.js): ${node_mem}% memory"
        
        # Check if memory usage is concerning
        local total_mem=$(echo "$python_mem + $node_mem" | bc 2>/dev/null || echo "0")
        if (( $(echo "$total_mem > 50" | bc -l 2>/dev/null || echo "0") )); then
            echo -e "  ${YELLOW}⚠ High memory usage detected${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Cannot check memory usage (ps not available)${NC}"
    fi
    
    # Check disk space
    if command -v df >/dev/null 2>&1; then
        local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
        echo "Disk usage: ${disk_usage}%"
        
        if [ "$disk_usage" -gt 80 ]; then
            echo -e "  ${YELLOW}⚠ High disk usage detected${NC}"
        fi
    fi
}

# Function to check log files
check_logs() {
    echo -e "\n${BLUE}Log Status${NC}"
    echo "----------"
    
    # Check if logs directory exists
    if [ -d "logs" ]; then
        echo "Recent log activity:"
        
        for service in fastapi nestjs nextjs; do
            if [ -f "logs/$service.log" ]; then
                local log_size=$(wc -l < "logs/$service.log" 2>/dev/null || echo "0")
                local last_modified=$(stat -f "%Sm" "logs/$service.log" 2>/dev/null || echo "unknown")
                echo -e "  $service: $log_size lines, last modified: $last_modified"
                
                # Check for recent errors
                local error_count=$(tail -100 "logs/$service.log" 2>/dev/null | grep -i "error\|exception\|failed" | wc -l || echo "0")
                if [ "$error_count" -gt 0 ]; then
                    echo -e "    ${YELLOW}⚠ $error_count recent errors found${NC}"
                fi
            else
                echo -e "  $service: ${YELLOW}⚠ Log file not found${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠ Logs directory not found${NC}"
    fi
}

# Function to check environment
check_environment() {
    echo -e "\n${BLUE}Environment Check${NC}"
    echo "-----------------"
    
    # Check environment files
    local env_files=(".env" "ai-chat-backend/.env" "ai-chat-frontend/.env.local")
    
    for env_file in "${env_files[@]}"; do
        if [ -f "$env_file" ]; then
            echo -e "✓ $env_file exists"
        else
            echo -e "${YELLOW}⚠ $env_file missing${NC}"
        fi
    done
    
    # Check for required environment variables
    if [ -f ".env" ]; then
        local required_vars=("OPENAI_API_KEY")
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" .env && ! grep -q "^$var=your-" .env; then
                echo -e "✓ $var is configured"
            else
                echo -e "${YELLOW}⚠ $var needs configuration${NC}"
            fi
        done
    fi
}

# Function to perform connectivity tests
check_connectivity() {
    echo -e "\n${BLUE}Connectivity Tests${NC}"
    echo "------------------"
    
    # Test internal connectivity
    echo -n "Testing NestJS to FastAPI connection... "
    local nestjs_health=$(curl -s "$NESTJS_URL/api/health" 2>/dev/null)
    
    if echo "$nestjs_health" | grep -q "fastapi.*true"; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${RED}✗ Connection failed${NC}"
    fi
    
    # Test external dependencies (if any)
    echo -n "Testing external connectivity... "
    if curl -s --connect-timeout 5 "https://api.openai.com" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ External services reachable${NC}"
    else
        echo -e "${YELLOW}⚠ External services unreachable${NC}"
    fi
}

# Main health check function
main() {
    local overall_status=0
    
    # Basic service health checks
    echo -e "${BLUE}Service Health${NC}"
    echo "-------------"
    
    check_endpoint "FastAPI" "$FASTAPI_URL/health" || overall_status=1
    check_endpoint "NestJS" "$NESTJS_URL/api/health" || overall_status=1
    check_endpoint "Next.js" "$NEXTJS_URL" || overall_status=1
    
    # Streaming functionality
    echo -e "\n${BLUE}Streaming Health${NC}"
    echo "---------------"
    
    check_streaming "FastAPI" "$FASTAPI_URL/api/chat/stream" || overall_status=1
    check_streaming "NestJS" "$NESTJS_URL/api/chat/stream" || overall_status=1
    
    # Extended checks
    check_api_functionality || overall_status=1
    check_connectivity || overall_status=1
    check_environment || overall_status=1
    check_resources
    check_logs
    
    # Summary
    echo -e "\n${BLUE}Health Check Summary${NC}"
    echo "==================="
    
    if [ $overall_status -eq 0 ]; then
        echo -e "${GREEN}🎉 All systems healthy!${NC}"
        echo ""
        echo "✅ All services are running correctly"
        echo "✅ Streaming functionality works"
        echo "✅ API endpoints are responsive"
        echo "✅ Internal connectivity is good"
    else
        echo -e "${RED}❌ Some issues detected!${NC}"
        echo ""
        echo "Please check the details above and:"
        echo "1. Ensure all services are running (./deploy.sh status)"
        echo "2. Check logs for errors (./deploy.sh logs)"
        echo "3. Verify environment configuration"
        echo "4. Restart services if needed (./deploy.sh stop && ./deploy.sh dev)"
    fi
    
    echo ""
    echo "For detailed troubleshooting, see README_NESTJS_NEXTJS.md"
    
    exit $overall_status
}

# Run the health check
main "$@"
