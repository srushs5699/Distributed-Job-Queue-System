#!/bin/bash

# Distributed Job Queue System - Setup Script
# This script sets up the complete environment

set -e

echo "========================================="
echo "Distributed Job Queue System - Setup"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check if Python is installed (for local development)
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
else
    echo -e "${YELLOW}⚠ Python 3 is not installed (required for local development only)${NC}"
fi

echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p tests
mkdir -p scripts

echo -e "${GREEN}✓ Directory structure created${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please review and update .env file with your configuration${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping${NC}"
fi

echo ""

# Build Docker images
echo "Building Docker images..."
docker-compose build
echo -e "${GREEN}✓ Docker images built successfully${NC}"

echo ""

# Start services
echo "Starting services..."
docker-compose up -d

echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check health
echo "Checking service health..."

# Check API
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running on http://localhost:5000${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
fi

# Check Grafana
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is running on http://localhost:3000${NC}"
else
    echo -e "${RED}✗ Grafana is not responding${NC}"
fi

# Check Prometheus
if curl -s http://localhost:9090 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is running on http://localhost:9090${NC}"
else
    echo -e "${RED}✗ Prometheus is not responding${NC}"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  - API:        http://localhost:5000"
echo "  - Grafana:    http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "Quick Start:"
echo "  1. Test the API:"
echo "     curl http://localhost:5000/health"
echo ""
echo "  2. Submit a job:"
echo "     make submit-job"
echo ""
echo "  3. View metrics:"
echo "     make metrics"
echo ""
echo "  4. Run benchmarks:"
echo "     make benchmark"
echo ""
echo "  5. View logs:"
echo "     make logs"
echo ""
echo "Useful commands:"
echo "  make help    - Show all available commands"
echo "  make down    - Stop all services"
echo "  make restart - Restart all services"
echo ""
echo "Documentation: See README.md for more information"
echo "========================================="