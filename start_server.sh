#!/bin/bash

# Start the FastAPI server
# This script starts the AI Business Advisor API server

echo "🚀 Starting AI Business Advisor FastAPI Server..."
echo "=================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if requirements are installed
echo "📋 Checking dependencies..."
pip list | grep -q fastapi
if [ $? -ne 0 ]; then
    echo "⚠️  FastAPI not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo "🌐 Starting server on http://localhost:8000..."
echo "📚 API documentation available at http://localhost:8000/docs"
echo "🔍 Health check available at http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

python main.py
