#!/bin/bash
# Start AetherCanon Builder MVP
# This script builds and runs the full application

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        AetherCanon Builder - MVP Startup Script         ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "Step 1: Checking Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running!${NC}"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    echo "To start Docker Desktop:"
    echo "  1. Open Docker Desktop application"
    echo "  2. Wait for the whale icon to appear in your menu bar"
    echo "  3. Verify Docker is running with: docker ps"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Build containers
echo "Step 2: Building Docker containers..."
echo "This will take 5-10 minutes on first run (downloads ~5GB)"
echo ""
docker-compose build
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# Start services
echo "Step 3: Starting services..."
echo "Starting: FastAPI backend, Streamlit frontend, Ollama"
echo ""
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be healthy
echo "Step 4: Waiting for services to be ready..."
sleep 10

# Check if Ollama is ready
echo "Checking Ollama service..."
for i in {1..30}; do
    if docker exec worldforge-ollama ollama list > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is ready${NC}"
        break
    fi
    echo "Waiting for Ollama... ($i/30)"
    sleep 2
done

# Pull Ollama model
echo ""
echo "Step 5: Downloading Ollama model (mistral:7b-instruct)..."
echo "This is ~4GB and will take 5-10 minutes depending on connection"
echo ""
docker exec worldforge-ollama ollama pull mistral:7b-instruct
echo -e "${GREEN}✓ Model downloaded${NC}"
echo ""

# Check application health
echo "Step 6: Verifying application health..."
sleep 5

# Check FastAPI
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ FastAPI backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠ FastAPI backend not responding yet (may need more time)${NC}"
fi

# Check Streamlit (it doesn't have a health endpoint, so just check if port is open)
if nc -z localhost 8501 2>/dev/null; then
    echo -e "${GREEN}✓ Streamlit frontend is running${NC}"
else
    echo -e "${YELLOW}⚠ Streamlit frontend not responding yet (may need more time)${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║                  🎉 STARTUP COMPLETE! 🎉                 ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Application URLs:"
echo "  📱 Frontend (Streamlit): http://localhost:8501"
echo "  🔧 Backend API:          http://localhost:8000"
echo "  📚 API Documentation:    http://localhost:8000/docs"
echo "  🤖 Ollama:               http://localhost:11434"
echo ""
echo "Quick Test:"
echo "  1. Open http://localhost:8501 in your browser"
echo "  2. Navigate to '📤 Upload Documents'"
echo "  3. Upload: tests/fixtures/documents/sample.md"
echo "  4. Wait for processing (~30-60 seconds)"
echo "  5. Navigate to '🔍 Query Your World'"
echo "  6. Ask: 'Who is Aragorn?'"
echo ""
echo "View Logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop Application:"
echo "  docker-compose down"
echo ""
echo "Happy worldbuilding! 🌍✨"
