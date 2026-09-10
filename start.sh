#!/bin/bash
set -e

echo "🚀 Starting Fluxline..."

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. 
    Please start Docker first."
  exit 1
fi

# Check .env exists
if [ ! -f .env ]; then
  echo "📋 Creating .env from .env.example..."
  cp .env.example .env
  echo "⚠️  Please edit .env and set:"
  echo "   JWT_SECRET_KEY=<random-string>"
  echo "   DEFAULT_ADMIN_PASSWORD=<password>"
  echo ""
  echo "Generate a secure key with:"
  echo "python -c \"import secrets; 
    print(secrets.token_hex(32))\""
  exit 1
fi

# Check JWT_SECRET_KEY is set
if grep -q "replace-this" .env; then
  echo "⚠️  Please set JWT_SECRET_KEY in .env"
  exit 1
fi

# Create data directory
mkdir -p data uploads

echo "🐋 Building and starting services..."
echo "⏱️  First run takes 5-10 minutes"
echo "    (downloading Ollama + llama3.1:8b)"
echo ""

docker-compose up --build -d

echo ""
echo "✅ Fluxline is starting!"
echo ""
echo "📊 Services:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   Ollama:    http://localhost:11434"
echo ""
echo "⏳ Waiting for Ollama model to download..."
echo "   Check progress: docker logs -f 
  fluxline-ollama-puller"
echo ""
echo "📋 View all logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"
