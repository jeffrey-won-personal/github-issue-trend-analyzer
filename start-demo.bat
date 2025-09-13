@echo off

REM GitHub Issue Trend Analyzer - Demo Mode Startup Script (Windows)
REM Runs the system without requiring any API keys

echo 🎭 Starting GitHub Issue Trend Analyzer in DEMO MODE...
echo ================================================
echo ✅ No API keys required!
echo ✅ Realistic mock data generated
echo ✅ All features fully functional
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Create demo environment file
echo 🔧 Setting up demo configuration...
(
echo # Demo Mode Configuration - No API Keys Required!
echo DEMO_MODE=true
echo.
echo # Application Configuration
echo ENVIRONMENT=development
echo LOG_LEVEL=INFO
echo API_HOST=0.0.0.0
echo API_PORT=8000
echo FRONTEND_PORT=3000
echo.
echo # Database ^(Optional - for agent memory persistence^)
echo DATABASE_URL=sqlite:///./data/agent_memory.db
) > .env

echo ✅ Demo configuration created

REM Build and start services
echo 🏗️  Building and starting services...
docker-compose down >nul 2>&1
docker-compose up -d --build

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 >nul

REM Check service health
echo 🔍 Checking service health...

REM Check backend
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend API failed to start
    docker-compose logs backend
    pause
    exit /b 1
) else (
    echo ✅ Backend API is running at http://localhost:8000
)

REM Check frontend
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Frontend may still be starting...
) else (
    echo ✅ Frontend is running at http://localhost:3000
)

echo.
echo 🎉 GitHub Issue Trend Analyzer is ready in DEMO MODE!
echo ================================================
echo 📱 Frontend:     http://localhost:3000
echo 🔧 Backend API:  http://localhost:8000
echo 📚 API Docs:     http://localhost:8000/docs
echo 🧪 Demo Page:    http://localhost:8000/demo
echo.
echo 🎭 DEMO MODE FEATURES:
echo    ✅ No API keys required
echo    ✅ Realistic mock data generated
echo    ✅ All agent features functional
echo    ✅ Real-time progress tracking
echo    ✅ Complete dashboard and reports
echo.
echo 💡 Try these demo repositories:
echo    • microsoft/vscode-demo
echo    • facebook/react-demo
echo    • tensorflow/tensorflow-demo
echo    • kubernetes/kubernetes-demo
echo.
echo To stop the services, run: docker-compose down
echo To view logs, run: docker-compose logs -f
echo.
echo Happy analyzing! 🚀
pause
