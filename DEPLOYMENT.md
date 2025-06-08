# FastAPI Backend Deployment Guide

This guide explains how to deploy the AI Business Advisor FastAPI backend as a service alongside your existing NestJS application.

## 🚀 Quick Deployment

### 1. Server Preparation

Run this on your server (where NestJS is already running):

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/your-repo/main/server-setup.sh | bash

# Or if you have the code:
chmod +x server-setup.sh
./server-setup.sh
```

### 2. Deploy Your Code

```bash
# Clone your repository to the server
cd /opt/ai-advisor
git clone <your-repo-url> .

# Configure environment variables
cp .env.production.template .env.production
nano .env.production  # Edit with your actual values

# Deploy the FastAPI backend
./deploy-backend.sh
```

## 📋 Configuration

### Environment Variables (.env.production)

```env
DATABASE_URL=postgresql://username:password@host:5432/database
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=production
STREAMING_ENABLED=true
STREAMING_DELAY=0.05
MAX_CONCURRENT_STREAMS=100
LOG_LEVEL=info
```

### NestJS Integration

Update your NestJS application to use the FastAPI backend:

```typescript
// In your NestJS configuration
const FASTAPI_URL = 'http://localhost:8000';

// Example service call
async callAiAdvisor(data: any) {
  const response = await fetch(`${FASTAPI_URL}/api/endpoint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return response.json();
}
```

## 🔧 Management Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop service
docker-compose -f docker-compose.prod.yml down

# Restart service
docker-compose -f docker-compose.prod.yml restart

# Check status
docker-compose -f docker-compose.prod.yml ps

# Update deployment
git pull
./deploy-backend.sh
```

## 🔍 Health Checks

The FastAPI service provides health endpoints:

- **Health Check**: `GET http://localhost:8000/health`
- **API Docs**: `GET http://localhost:8000/docs` (in development)

## 📊 Service Details

- **Port**: 8000
- **Container Name**: ai-advisor-api
- **Data Persistence**: `./data` and `./logs` directories
- **Auto-restart**: Yes (unless-stopped)
- **Health Monitoring**: Built-in Docker health checks

## 🔥 Firewall Configuration

Make sure port 8000 is accessible:

```bash
# Ubuntu/Debian with UFW
sudo ufw allow 8000/tcp

# CentOS/RHEL with firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

### Database Connection Issues

```bash
# Test database connectivity from container
docker-compose -f docker-compose.prod.yml exec ai-advisor-api psql $DATABASE_URL
```

### Environment Variables Not Loading

```bash
# Verify environment file
cat .env.production

# Check if variables are loaded in container
docker-compose -f docker-compose.prod.yml exec ai-advisor-api env | grep DATABASE_URL
```

## 📝 Logs

Application logs are available in:

- Container logs: `docker-compose -f docker-compose.prod.yml logs`
- File logs: `./logs/` directory (mounted from container)

## 🔄 Updates

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart
./deploy-backend.sh
```

This will build a new image and restart the service with zero downtime health checks.
