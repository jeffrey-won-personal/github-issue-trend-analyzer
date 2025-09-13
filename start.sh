#!/bin/bash

# GitHub Issue Trend Analyzer - One-Click Startup Script

echo "🚀 Starting GitHub Issue Trend Analyzer..."
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists, if not offer demo mode
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found."
    echo ""
    echo "Choose an option:"
    echo "1) Create .env file and configure with your API keys"
    echo "2) Run in DEMO MODE (no API keys required)"
    echo ""
    read -p "Enter your choice (1 or 2): " choice
    
    case $choice in
        1)
            cp .env.example .env
            echo "📝 Please edit .env file with your API keys:"
            echo "   - OPENAI_API_KEY (required)"
            echo "   - GITHUB_TOKEN (optional but recommended)"
            echo ""
            echo "Then run this script again."
            exit 1
            ;;
        2)
            echo "🎭 Starting in DEMO MODE..."
            cp .env.demo .env
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# Check if we're in demo mode
source .env
if [ "$DEMO_MODE" = "true" ]; then
    echo "🎭 Running in DEMO MODE - no API keys required!"
    echo "   Using realistic mock data to showcase all features"
else
    # Check if required environment variables are set for production mode
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ Error: OPENAI_API_KEY is not set in .env file"
        echo "💡 Tip: Set DEMO_MODE=true in .env to run without API keys"
        exit 1
    fi
fi

echo "✅ Environment configuration validated"

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose down 2>/dev/null  # Stop any existing containers
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is running at http://localhost:8000"
else
    echo "❌ Backend API failed to start"
    docker-compose logs backend
    exit 1
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "🎉 GitHub Issue Trend Analyzer is ready!"
echo "================================================"
echo "📱 Frontend:     http://localhost:3000"
echo "🔧 Backend API:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "🧪 Demo Page:    http://localhost:8000/demo"
echo ""

# Show mode-specific info
if [ "$DEMO_MODE" = "true" ]; then
    echo "🎭 DEMO MODE ACTIVE:"
    echo "   ✅ No API keys required"
    echo "   ✅ Realistic mock data generated"
    echo "   ✅ All features fully functional"
    echo "   💡 Try: microsoft/vscode-demo, facebook/react-demo, or tensorflow/tensorflow-demo"
else
    echo "🚀 PRODUCTION MODE:"
    echo "   ✅ Real GitHub API integration"
    echo "   ✅ OpenAI-powered insights"
    echo "   💡 Try: microsoft/vscode, facebook/react, or tensorflow/tensorflow"
fi

echo ""
echo "To stop the services, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"
echo ""
echo "Happy analyzing! 🚀"
