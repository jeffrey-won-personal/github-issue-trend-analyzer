"""
Main entry point for the GitHub Issue Trend Analyzer.
Multi-agent system using LangGraph for intelligent repository analysis.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the FastAPI app
from src.api.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Run the application
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=environment == "development",
        log_level="info"
    )


