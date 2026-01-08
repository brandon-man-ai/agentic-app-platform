#!/bin/bash

# Agentic App Platform - Docker Startup Script

set -e

echo "🚀 Starting Agentic App Platform..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please copy docker.env.example to .env and add your API keys:"
    echo "   cp docker.env.example .env"
    exit 1
fi

# Check if E2B_API_KEY is set
if ! grep -q "E2B_API_KEY=." .env 2>/dev/null; then
    echo "⚠️  Warning: E2B_API_KEY may not be set in .env"
fi

# Build and start containers
echo "📦 Building Docker containers..."
docker-compose build

echo "🐳 Starting services..."
docker-compose up -d

echo ""
echo "✅ Agentic App Platform is running!"
echo ""
echo "   Frontend: http://localhost:3002"
echo "   Backend:  http://localhost:8002"
echo ""
echo "   View logs: docker-compose logs -f"
echo "   Stop:      docker-compose down"
echo ""

