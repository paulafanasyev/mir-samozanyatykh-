#!/bin/bash
# Auto-deploy script for Render.com
# MIR Samozanyatykh v8.4 - ANO TsPS INN 9724016805
# Blueprint ID: exs-da08tgtbedkc73a743pg

set -e

echo "=========================================="
echo "  DEPLOY TO RENDER.COM"
echo "  MIR Samozanyatykh v8.4"
echo "=========================================="
echo ""

# Check if RENDER_API_KEY is set
if [ -z "$RENDER_API_KEY" ]; then
    echo "ERROR: RENDER_API_KEY is not set!"
    echo ""
    echo "To get your API key:"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Click your profile → Account Settings"
    echo "3. Scroll to API Keys → Create API Key"
    echo "4. Copy the key and run: export RENDER_API_KEY=your_key"
    echo ""
    exit 1
fi

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo "Installing Render CLI..."
    curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
    export PATH="$PATH:$HOME/.render"
fi

# Login to Render
echo "Logging in to Render..."
render login

echo ""
echo "=========================================="
echo "  Creating services from render.yaml"
echo "=========================================="
echo ""

# Deploy using Blueprint
render blueprint apply ./render.yaml

echo ""
echo "=========================================="
echo "  DEPLOYMENT INITIATED!"
echo "=========================================="
echo ""
echo "Check status at: https://dashboard.render.com"
echo ""
echo "Services created:"
echo "  - PostgreSQL: mirsamozanyatykh-db"
echo "  - Redis: mirsamozanyatykh-redis"
echo "  - Backend: mirsamozanyatykh-api"
echo "  - Frontend: mirsamozanyatykh"
echo ""
