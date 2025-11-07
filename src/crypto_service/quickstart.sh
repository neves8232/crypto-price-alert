#!/bin/bash
# Quick Start Script for Crypto Price Alert Service
# This script helps you get started quickly with the service

set -e

echo "=========================================="
echo "Crypto Price Alert Service - Quick Start"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the crypto_service directory${NC}"
    exit 1
fi

# Step 1: Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.11+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${YELLOW}[2/7] Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Step 3: Activate and install dependencies
echo -e "${YELLOW}[3/7] Installing dependencies...${NC}"
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Setup environment file
echo -e "${YELLOW}[4/7] Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env

    # Generate auth token
    AUTH_TOKEN=$(openssl rand -hex 32)

    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/AUTH_TOKEN=.*/AUTH_TOKEN=$AUTH_TOKEN/" .env
    else
        # Linux
        sed -i "s/AUTH_TOKEN=.*/AUTH_TOKEN=$AUTH_TOKEN/" .env
    fi

    echo -e "${GREEN}✓ Environment file created with generated auth token${NC}"
    echo -e "${YELLOW}  Note: Update TELEGRAM_SERVICE_URL if needed${NC}"
else
    echo -e "${GREEN}✓ Environment file already exists${NC}"
fi
echo ""

# Step 5: Initialize database
echo -e "${YELLOW}[5/7] Initializing database...${NC}"
if [ ! -f "crypto_alerts.db" ]; then
    alembic upgrade head
    echo -e "${GREEN}✓ Database initialized with migrations${NC}"
else
    echo -e "${YELLOW}  Database already exists. Run 'alembic upgrade head' to apply new migrations.${NC}"
fi
echo ""

# Step 6: Add sample cryptocurrency
echo -e "${YELLOW}[6/7] Setup complete! Starting service...${NC}"
echo ""

# Step 7: Instructions
echo -e "${GREEN}=========================================="
echo -e "Installation Complete!"
echo -e "==========================================${NC}"
echo ""
echo "To start the service:"
echo -e "${YELLOW}  source venv/bin/activate${NC}"
echo -e "${YELLOW}  python -m uvicorn crypto_service.main:app --host 0.0.0.0 --port 52000${NC}"
echo ""
echo "Or start with auto-reload (development):"
echo -e "${YELLOW}  source venv/bin/activate${NC}"
echo -e "${YELLOW}  python -m uvicorn crypto_service.main:app --host 0.0.0.0 --port 52000 --reload${NC}"
echo ""
echo "API Documentation:"
echo "  http://localhost:52000/docs"
echo ""
echo "Health Check:"
echo "  http://localhost:52000/health"
echo ""
echo "Example: Add Bitcoin to watchlist"
echo "  curl -X POST http://localhost:52000/api/cryptocurrencies \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"crypto_id\": \"bitcoin\", \"symbol\": \"BTC\", \"name\": \"Bitcoin\"}'"
echo ""
echo -e "${YELLOW}Note: Prices will start collecting within 15 seconds of startup.${NC}"
echo ""
echo "For more information, see:"
echo "  - README.md for full documentation"
echo "  - TESTING.md for testing procedures"
echo "  - IMPLEMENTATION_SUMMARY.md for technical details"
echo ""
