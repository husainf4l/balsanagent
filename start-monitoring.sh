#!/bin/bash

# Start Monitoring Stack for AI Business Advisor
echo "🚀 Starting Monitoring Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose -f docker-compose.monitoring.yml down

# Start the monitoring stack
echo "📊 Starting Prometheus and Grafana..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "✅ Monitoring Stack Started!"
echo ""
echo "📊 Access your monitoring tools:"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana:    http://localhost:3000 (admin/admin123)"
echo "   • FastAPI:    http://localhost:8000"
echo ""
echo "🔧 Grafana Setup:"
echo "   1. Login with admin/admin123"
echo "   2. Prometheus datasource is pre-configured"
echo "   3. AI Chat dashboard should be available"
echo ""
echo "🛑 To stop: docker-compose -f docker-compose.monitoring.yml down"
