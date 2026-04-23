#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "🚀 Starting Crypto Scalping Bot in Docker..."

# Check if .env exists, if not create from .env.example
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please make sure to update it with your Binance API keys later."
    else
        echo "❌ .env.example also not found. Please create a .env file with your configuration."
        exit 1
    fi
fi

# Run docker compose
echo "🐳 Building and starting Docker container..."
docker compose up --build -d

if [ $? -eq 0 ]; then
    echo "✅ Docker container started successfully!"
    echo "⏳ Waiting for the web server to start..."
    
    # Wait a few seconds for the web server inside the container to be ready
    sleep 5
    
    echo "🌐 Opening web interface in your default browser..."
    
    # Open browser (macOS uses "open")
    if command -v open &> /dev/null; then
        open http://localhost:8766
    else
        echo "👉 Please open http://localhost:8766 in your web browser."
    fi
    
    echo ""
    echo "📜 To view live logs, run: docker compose logs -f"
    echo "⏹️  To stop the bot, run: docker compose down"
else
    echo "❌ Failed to start Docker container. Please check if Docker Desktop is running."
    exit 1
fi
