#!/bin/bash
# Quick Docker status check

echo "Checking Docker status..."
echo ""

if docker ps > /dev/null 2>&1; then
    echo "✅ Docker is running!"
    echo ""
    echo "Docker version:"
    docker --version
    echo ""
    echo "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "🚀 Ready to start the MVP!"
    echo "Run: ./start-mvp.sh"
else
    echo "❌ Docker is NOT running"
    echo ""
    echo "Please start Docker Desktop:"
    echo "  1. Press Cmd+Space"
    echo "  2. Type 'Docker'"
    echo "  3. Press Enter"
    echo "  4. Wait for Docker to start (whale icon in menu bar)"
    echo "  5. Run this script again: ./check-docker.sh"
fi
