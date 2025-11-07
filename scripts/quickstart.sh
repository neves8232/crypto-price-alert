#!/bin/bash
# ================================================================
# Crypto Price Alert System - Quick Start Script
# ================================================================
# This script helps you get started quickly with the system
# ================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}Crypto Price Alert - Quick Start${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found:${NC} $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found:${NC} $(docker-compose --version)"

echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}======================================${NC}"
    echo -e "${YELLOW}IMPORTANT: Configure your .env file!${NC}"
    echo -e "${YELLOW}======================================${NC}"
    echo ""
    echo "Please edit the .env file and set the following required values:"
    echo ""
    echo "1. TELEGRAM_BOT_TOKEN - Get from @BotFather on Telegram"
    echo "2. AUTH_TOKEN - Generate with: openssl rand -hex 32"
    echo "3. POSTGRES_PASSWORD - Set a strong password"
    echo ""
    echo -e "${CYAN}Press Enter after you've configured .env, or Ctrl+C to exit...${NC}"
    read -r
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Validate critical environment variables
echo ""
echo -e "${YELLOW}Validating environment variables...${NC}"

source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_from_botfather" ]; then
    echo -e "${RED}✗ TELEGRAM_BOT_TOKEN is not configured${NC}"
    echo "Please edit .env and set TELEGRAM_BOT_TOKEN"
    exit 1
fi
echo -e "${GREEN}✓ TELEGRAM_BOT_TOKEN is set${NC}"

if [ -z "$AUTH_TOKEN" ] || [ "$AUTH_TOKEN" = "your_secure_random_token_here_minimum_32_characters" ]; then
    echo -e "${RED}✗ AUTH_TOKEN is not configured${NC}"
    echo "Generate one with: openssl rand -hex 32"
    exit 1
fi

if [ ${#AUTH_TOKEN} -lt 32 ]; then
    echo -e "${RED}✗ AUTH_TOKEN is too short (minimum 32 characters)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AUTH_TOKEN is set${NC}"

echo ""

# Ask deployment mode
echo -e "${CYAN}Select deployment mode:${NC}"
echo "1) Development (SQLite, debug logging, hot reload)"
echo "2) Production (PostgreSQL, optimized settings)"
echo ""
read -p "Enter choice [1-2]: " mode

case $mode in
    1)
        echo ""
        echo -e "${CYAN}Starting in DEVELOPMENT mode...${NC}"
        echo ""

        # Create data directory for SQLite
        mkdir -p data

        # Start development
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

        echo ""
        echo -e "${GREEN}✓ Services started in development mode${NC}"
        ;;
    2)
        echo ""
        echo -e "${CYAN}Starting in PRODUCTION mode...${NC}"
        echo ""

        # Validate PostgreSQL password
        if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "secure_password_here_change_in_production" ]; then
            echo -e "${RED}✗ POSTGRES_PASSWORD is not configured for production${NC}"
            echo "Please edit .env and set a strong POSTGRES_PASSWORD"
            exit 1
        fi

        # Start production
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

        echo ""
        echo -e "${GREEN}✓ Services started in production mode${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Wait for services to start
echo ""
echo -e "${YELLOW}Waiting for services to start (30 seconds)...${NC}"
sleep 30

# Check service status
echo ""
echo -e "${CYAN}Service Status:${NC}"
docker-compose ps

# Test health endpoints
echo ""
echo -e "${CYAN}Testing health endpoints...${NC}"

if curl -sf http://localhost:52000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Crypto Service is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Crypto Service health check pending...${NC}"
fi

if curl -sf http://localhost:52001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Telegram Service is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Telegram Service health check pending...${NC}"
fi

# Success message
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${CYAN}Access your services:${NC}"
echo "  Web UI:       http://localhost:52000"
echo "  API Docs:     http://localhost:52000/docs"
echo "  Health Check: http://localhost:52000/health"
echo ""
echo -e "${CYAN}Useful commands:${NC}"
echo "  View logs:    docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart:      docker-compose restart"
echo ""
echo -e "${CYAN}For more information:${NC}"
echo "  Documentation: docs/deployment/DOCKER_GUIDE.md"
echo "  Run 'make help' for all available commands"
echo ""
