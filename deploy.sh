#!/bin/bash

# WB AutoSlot Deployment Script

set -e

echo "🚀 WB AutoSlot Deployment Script"
echo "================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check environment
ENVIRONMENT=${1:-development}

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Deploying to PRODUCTION environment"
    COMPOSE_FILE="docker-compose.prod.yml"
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "❌ .env file not found for production deployment"
        echo "Please create .env file with production configuration"
        exit 1
    fi
    
    # Check required environment variables
    required_vars=("SECRET_KEY" "JWT_SECRET_KEY" "POSTGRES_PASSWORD")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            echo "❌ Required environment variable $var not found in .env"
            exit 1
        fi
    done
    
else
    echo "🔧 Deploying to DEVELOPMENT environment"
    COMPOSE_FILE="docker-compose.yml"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from example..."
        cp env.example .env
        echo "⚠️  Please edit .env file with your configuration"
    fi
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down || true

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Build images
echo "🔨 Building images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health check
echo "🏥 Performing health check..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "✅ API is healthy"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts - Waiting for API..."
        sleep 10
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Health check failed after $max_attempts attempts"
    echo "📋 Checking logs..."
    docker-compose -f $COMPOSE_FILE logs --tail=50
    exit 1
fi

# Run tests
echo "🧪 Running API tests..."
if [ -f test_api.py ]; then
    python3 test_api.py
    if [ $? -eq 0 ]; then
        echo "✅ All tests passed"
    else
        echo "⚠️  Some tests failed, but deployment continues"
    fi
else
    echo "ℹ️  Test script not found, skipping tests"
fi

# Show status
echo "📊 Deployment Status:"
echo "===================="
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 API: http://localhost:5000"
echo "📊 Health: http://localhost:5000/api/health"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
echo "  Update services: docker-compose -f $COMPOSE_FILE pull && docker-compose -f $COMPOSE_FILE up -d"
