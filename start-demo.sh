#!/bin/bash

# GitHub Issue Trend Analyzer - Demo Mode Startup Script
# Runs the system without requiring any API keys

echo "🎭 Starting GitHub Issue Trend Analyzer in DEMO MODE..."
echo "================================================"
echo "✅ No API keys required!"
echo "✅ Realistic mock data generated"
echo "✅ All features fully functional"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create demo environment file
echo "🔧 Setting up demo configuration..."
cat > .env << EOF
# Demo Mode Configuration - No API Keys Required!
DEMO_MODE=true

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3000

# Database (Optional - for agent memory persistence)
DATABASE_URL=sqlite:///./data/agent_memory.db
EOF

echo "✅ Demo configuration created"

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
echo "🎉 GitHub Issue Trend Analyzer is ready in DEMO MODE!"
echo "================================================"
echo "📱 Frontend:     http://localhost:3000"
echo "🔧 Backend API:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "🧪 Demo Page:    http://localhost:8000/demo"
echo ""
echo "🎭 DEMO MODE FEATURES:"
echo "   ✅ No API keys required"
echo "   ✅ Realistic mock data generated"
echo "   ✅ All agent features functional"
echo "   ✅ Real-time progress tracking"
echo "   ✅ Complete dashboard and reports"
echo ""
echo "💡 Try these demo repositories:"
echo "   • microsoft/vscode-demo"
echo "   • facebook/react-demo"
echo "   • tensorflow/tensorflow-demo"
echo "   • kubernetes/kubernetes-demo"
echo ""
echo "To stop the services, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"
echo ""
echo "Happy analyzing! 🚀"


