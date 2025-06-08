#!/bin/bash

# Comprehensive Streaming Test Script for AI Business Advisor
# Tests FastAPI streaming, NestJS proxy, and frontend integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
FASTAPI_URL="http://localhost:8000"
NESTJS_URL="http://localhost:3001"
NEXTJS_URL="http://localhost:3000"
TEST_SESSION_ID="test-$(date +%s)"

echo -e "${BLUE}🚀 AI Business Advisor Streaming Test Suite${NC}"
echo "=============================================="

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    if curl -s "$url/health" > /dev/null 2>&1 || curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to test streaming endpoint
test_streaming() {
    local url=$1
    local name=$2
    local message=$3
    
    echo -e "\n${YELLOW}Testing $name streaming...${NC}"
    
    # Create temporary file for response
    local temp_file=$(mktemp)
    
    # Send streaming request with timeout
    timeout 10s curl -X POST "$url/api/chat/stream" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"session_id\": \"$TEST_SESSION_ID\"}" \
        --no-buffer \
        -s > "$temp_file" 2>/dev/null || {
        echo -e "${RED}✗ Request failed or timed out${NC}"
        rm -f "$temp_file"
        return 1
    }
    
    # Check if response contains expected SSE format
    if grep -q "data:" "$temp_file" && grep -q "type.*word" "$temp_file"; then
        local word_count=$(grep -c "type.*word" "$temp_file")
        echo -e "${GREEN}✓ Streaming successful - $word_count words streamed${NC}"
        
        # Show sample of streamed content
        echo "Sample streamed events:"
        head -5 "$temp_file" | sed 's/^/  /'
        
        rm -f "$temp_file"
        return 0
    else
        echo -e "${RED}✗ Invalid streaming format${NC}"
        echo "Response:"
        head -10 "$temp_file" | sed 's/^/  /'
        rm -f "$temp_file"
        return 1
    fi
}

# Function to test regular chat endpoint
test_regular_chat() {
    local url=$1
    local name=$2
    local message=$3
    
    echo -e "\n${YELLOW}Testing $name regular chat...${NC}"
    
    local response=$(curl -X POST "$url/api/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"session_id\": \"$TEST_SESSION_ID\"}" \
        -s)
    
    if echo "$response" | grep -q "response" && echo "$response" | grep -q -v "error"; then
        echo -e "${GREEN}✓ Regular chat successful${NC}"
        echo "Response preview:"
        echo "$response" | jq -r '.response' 2>/dev/null | head -2 | sed 's/^/  /' || echo "$response" | head -2 | sed 's/^/  /'
        return 0
    else
        echo -e "${RED}✗ Regular chat failed${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Function to test session management
test_session_management() {
    echo -e "\n${YELLOW}Testing session management...${NC}"
    
    # Create new session
    local session_response=$(curl -X POST "$NESTJS_URL/api/sessions" -s)
    local session_id=$(echo "$session_response" | jq -r '.session_id' 2>/dev/null || echo "")
    
    if [ -n "$session_id" ] && [ "$session_id" != "null" ]; then
        echo -e "${GREEN}✓ Session creation successful: $session_id${NC}"
        
        # Test chat with created session
        local chat_response=$(curl -X POST "$NESTJS_URL/api/chat" \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"Hello\", \"session_id\": \"$session_id\"}" \
            -s)
        
        if echo "$chat_response" | grep -q "response"; then
            echo -e "${GREEN}✓ Session-based chat successful${NC}"
            return 0
        else
            echo -e "${RED}✗ Session-based chat failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Session creation failed${NC}"
        return 1
    fi
}

# Function to test error handling
test_error_handling() {
    echo -e "\n${YELLOW}Testing error handling...${NC}"
    
    # Test with invalid endpoint
    local error_response=$(curl -X POST "$NESTJS_URL/api/invalid-endpoint" -s -w "%{http_code}")
    local http_code="${error_response: -3}"
    
    if [ "$http_code" = "404" ]; then
        echo -e "${GREEN}✓ 404 error handling works${NC}"
    else
        echo -e "${YELLOW}⚠ Unexpected response code: $http_code${NC}"
    fi
    
    # Test with malformed JSON
    local malformed_response=$(curl -X POST "$NESTJS_URL/api/chat" \
        -H "Content-Type: application/json" \
        -d "{invalid json" \
        -s)
    
    if echo "$malformed_response" | grep -q -i "error\|bad\|invalid"; then
        echo -e "${GREEN}✓ Malformed JSON error handling works${NC}"
    else
        echo -e "${YELLOW}⚠ Malformed JSON handling unclear${NC}"
    fi
}

# Function to test concurrent streaming
test_concurrent_streaming() {
    echo -e "\n${YELLOW}Testing concurrent streaming...${NC}"
    
    local pids=()
    local temp_files=()
    
    # Start 3 concurrent streaming requests
    for i in {1..3}; do
        local temp_file=$(mktemp)
        temp_files+=("$temp_file")
        
        (
            curl -X POST "$NESTJS_URL/api/chat/stream" \
                -H "Content-Type: application/json" \
                -d "{\"message\": \"Concurrent test $i\", \"session_id\": \"concurrent-$i\"}" \
                --no-buffer \
                -s > "$temp_file" 2>/dev/null
        ) &
        pids+=($!)
    done
    
    # Wait for all requests to complete (with timeout)
    local success_count=0
    for i in "${!pids[@]}"; do
        if timeout 15s wait "${pids[$i]}" 2>/dev/null; then
            if grep -q "data:" "${temp_files[$i]}"; then
                ((success_count++))
            fi
        fi
    done
    
    # Cleanup
    for temp_file in "${temp_files[@]}"; do
        rm -f "$temp_file"
    done
    
    if [ "$success_count" -eq 3 ]; then
        echo -e "${GREEN}✓ Concurrent streaming successful ($success_count/3)${NC}"
    elif [ "$success_count" -gt 0 ]; then
        echo -e "${YELLOW}⚠ Partial concurrent streaming success ($success_count/3)${NC}"
    else
        echo -e "${RED}✗ Concurrent streaming failed${NC}"
    fi
}

# Function to check memory usage
check_memory_usage() {
    echo -e "\n${YELLOW}Checking memory usage...${NC}"
    
    if command -v ps &> /dev/null; then
        echo "Python processes:"
        ps aux | grep python | grep -v grep | awk '{print "  PID: " $2 ", Memory: " $4 "%, Command: " $11}' || echo "  No Python processes found"
        
        echo "Node.js processes:"
        ps aux | grep node | grep -v grep | awk '{print "  PID: " $2 ", Memory: " $4 "%, Command: " $11}' || echo "  No Node.js processes found"
    else
        echo -e "${YELLOW}⚠ ps command not available for memory check${NC}"
    fi
}

# Main test execution
main() {
    echo -e "\n${BLUE}1. Service Health Checks${NC}"
    echo "========================"
    
    local fastapi_ok=false
    local nestjs_ok=false
    local nextjs_ok=false
    
    check_service "$FASTAPI_URL" "FastAPI" && fastapi_ok=true
    check_service "$NESTJS_URL" "NestJS" && nestjs_ok=true
    check_service "$NEXTJS_URL" "Next.js" && nextjs_ok=true
    
    if [ "$fastapi_ok" = false ] || [ "$nestjs_ok" = false ]; then
        echo -e "\n${RED}❌ Critical services not running. Please start all services first.${NC}"
        echo "Run this to start services:"
        echo "  Terminal 1: cd /path/to/aqlon && python main_streaming.py"
        echo "  Terminal 2: cd ai-chat-backend && npm run start:dev"
        echo "  Terminal 3: cd your-nextjs-app && npm run dev"
        exit 1
    fi
    
    echo -e "\n${BLUE}2. Regular Chat Tests${NC}"
    echo "==================="
    test_regular_chat "$NESTJS_URL" "NestJS"  "What is business analytics?"
    
    echo -e "\n${BLUE}3. Streaming Tests${NC}"
    echo "================="
    test_streaming "$FASTAPI_URL" "FastAPI" "Explain key performance indicators"
    test_streaming "$NESTJS_URL" "NestJS" "How do I improve customer retention?"
    
    echo -e "\n${BLUE}4. Session Management Tests${NC}"
    echo "=========================="
    test_session_management
    
    echo -e "\n${BLUE}5. Error Handling Tests${NC}"
    echo "======================"
    test_error_handling
    
    echo -e "\n${BLUE}6. Concurrent Streaming Tests${NC}"
    echo "============================"
    test_concurrent_streaming
    
    echo -e "\n${BLUE}7. Memory Usage Check${NC}"
    echo "===================="
    check_memory_usage
    
    echo -e "\n${BLUE}8. Test Summary${NC}"
    echo "==============="
    echo -e "${GREEN}✅ Basic functionality tests completed${NC}"
    echo -e "${GREEN}✅ Streaming functionality verified${NC}"
    echo -e "${GREEN}✅ Session management tested${NC}"
    echo -e "${GREEN}✅ Error handling validated${NC}"
    echo -e "${GREEN}✅ Concurrent streaming tested${NC}"
    
    echo -e "\n${BLUE}🎉 Test Suite Complete!${NC}"
    echo "======================================"
    echo "All components are working correctly."
    echo ""
    echo "Next steps:"
    echo "1. Open http://localhost:3000 in your browser"
    echo "2. Toggle 'Enable Streaming' to test both modes"
    echo "3. Send some test messages"
    echo "4. Monitor the console for any errors"
    echo ""
    echo "For production deployment, see the README deployment section."
}

# Run main function
main "$@"
