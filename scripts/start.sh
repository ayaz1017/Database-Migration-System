#!/bin/bash
set -e

echo "══════════════════════════════════════"
echo "  Starting Fluxline..."
echo "══════════════════════════════════════"

# Check .env.docker exists
if [ ! -f .env.docker ]; then
  echo "ERROR: .env.docker not found"
  echo "Run: cp .env.docker.example .env.docker"
  echo "Then edit .env.docker with your values."
  exit 1
fi

# Start services
docker compose --env-file .env.docker up -d --build

echo ""
echo "Waiting for services to start..."
sleep 10

# Show status
docker compose ps

echo ""
echo "══════════════════════════════════════"
echo "  Fluxline is running!"
echo "══════════════════════════════════════"
echo ""
echo "  Frontend:    http://localhost"
echo "  Backend API: http://localhost:8000"
echo "  Ollama:      http://localhost:11434"
echo ""
echo "  First run? Ollama is downloading the"
echo "  model (~4.7GB) in the background."
echo "  Check progress:"
echo "    docker logs fluxline-ollama-setup -f"
echo ""
