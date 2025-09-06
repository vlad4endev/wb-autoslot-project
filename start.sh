#!/bin/bash

# WB AutoSlot Startup Script

echo "🚀 Starting WB AutoSlot..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "📦 Docker detected. Starting with Docker Compose..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Creating from example..."
        cp env.example .env
        echo "📝 Please edit .env file with your configuration"
    fi
    
    # Start with Docker Compose
    docker-compose up -d
    
    echo "✅ WB AutoSlot started with Docker!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 API: http://localhost:5000"
    
else
    echo "🐍 Docker not found. Starting manually..."
    
    # Start Backend
    echo "🔧 Starting Backend..."
    cd wb-autoslot-api
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    
    # Install Playwright browsers
    echo "🎭 Installing Playwright browsers..."
    playwright install chromium
    
    # Start backend
    echo "🚀 Starting backend server..."
    python src/main.py &
    BACKEND_PID=$!
    
    # Start Frontend
    echo "🎨 Starting Frontend..."
    cd ../wb-autoslot-frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install -g pnpm
        pnpm install
    fi
    
    # Start frontend
    echo "🚀 Starting frontend server..."
    pnpm dev &
    FRONTEND_PID=$!
    
    echo "✅ WB AutoSlot started manually!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 API: http://localhost:5000"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
fi
