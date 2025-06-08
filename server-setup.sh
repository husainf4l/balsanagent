#!/bin/bash

# Simple Server Setup Script for AI Business Advisor FastAPI Backend
# Run this script on your server where NestJS is already running

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up server for AI Business Advisor FastAPI Backend${NC}"
echo "=============================================================="

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

# Update system
echo -e "${BLUE}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y
print_status "System updated"

# Install Docker if not already installed
echo -e "${BLUE}🐳 Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_status "Docker installed"
else
    print_status "Docker already installed"
fi

# Install Docker Compose if not already installed
echo -e "${BLUE}🔧 Checking Docker Compose installation...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed"
else
    print_status "Docker Compose already installed"
fi

# Install Git if not already installed
echo -e "${BLUE}📋 Checking Git installation...${NC}"
if ! command -v git &> /dev/null; then
    sudo apt install git -y
    print_status "Git installed"
else
    print_status "Git already installed"
fi

# Install useful tools
echo -e "${BLUE}🛠 Installing useful tools...${NC}"
sudo apt install htop curl wget unzip -y
print_status "Tools installed"

# Configure firewall to allow FastAPI port
echo -e "${BLUE}🔥 Configuring firewall for FastAPI...${NC}"
if command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp
    print_status "Port 8000 allowed in firewall"
else
    print_warning "UFW not found, make sure port 8000 is open"
fi

# Create application directory
echo -e "${BLUE}📁 Creating application directory...${NC}"
sudo mkdir -p /opt/ai-advisor
sudo chown $USER:$USER /opt/ai-advisor
print_status "Application directory created at /opt/ai-advisor"

echo -e "${GREEN}🎉 Server setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Clone your repository:"
echo "   cd /opt/ai-advisor"
echo "   git clone <your-repo-url> ."
echo ""
echo "2. Copy environment template and configure:"
echo "   cp .env.production.template .env.production"
echo "   nano .env.production  # Edit with your actual values"
echo ""
echo "3. Deploy the FastAPI backend:"
echo "   ./deploy-backend.sh"
echo ""
echo -e "${YELLOW}Note: You may need to log out and back in for Docker group membership to take effect${NC}"
