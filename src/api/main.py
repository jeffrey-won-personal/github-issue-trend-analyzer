"""
FastAPI application for the GitHub Issue Trend Analyzer.
Provides REST API and WebSocket endpoints for the multi-agent system.
"""

import os
import asyncio
import json
from typing import Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from ..core.orchestrator import MultiAgentOrchestrator
from ..core.state import WorkflowState


# Pydantic models for API
class AnalysisRequest(BaseModel):
    repository_url: str = Field(..., description="GitHub repository URL")
    analysis_period_days: int = Field(default=90, ge=1, le=365, description="Analysis period in days")
    include_closed_issues: bool = Field(default=True, description="Include closed issues in analysis")


class AnalysisResponse(BaseModel):
    session_id: str
    status: str
    message: str


class SessionStatus(BaseModel):
    session_id: str
    current_step: str
    completion_percentage: float
    agent_statuses: dict
    latest_update: Optional[dict] = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"🔌 WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_update(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            try:
                print(f"📤 Sending WebSocket update to session {session_id}: {data}")
                await self.active_connections[session_id].send_text(json.dumps(data))
            except Exception as e:
                print(f"❌ Error sending WebSocket update: {e}")
                self.disconnect(session_id)
        else:
            print(f"⚠️ No active WebSocket connection for session {session_id}")


# Initialize FastAPI app
app = FastAPI(
    title="GitHub Issue Trend Analyzer",
    description="Multi-agent system for analyzing GitHub repository issue trends",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
orchestrator: Optional[MultiAgentOrchestrator] = None
connection_manager = ConnectionManager()
active_sessions: dict[str, WorkflowState] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup."""
    global orchestrator
    
    # Check if we're in demo mode
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if demo_mode:
        orchestrator = MultiAgentOrchestrator(demo_mode=True)
        print("🎭 Multi-agent orchestrator initialized in DEMO MODE")
        print("   No API keys required - using realistic mock data")
    else:
        if not openai_api_key:
            print("⚠️  No OPENAI_API_KEY found. Starting in demo mode...")
            orchestrator = MultiAgentOrchestrator(demo_mode=True)
            print("🎭 Multi-agent orchestrator initialized in DEMO MODE")
        else:
            orchestrator = MultiAgentOrchestrator(openai_api_key)
            print("🚀 Multi-agent orchestrator initialized successfully")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GitHub Issue Trend Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze",
            "status": "/status/{session_id}",
            "results": "/results/{session_id}",
            "websocket": "/ws/{session_id}"
        }
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start a new analysis workflow."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Validate repository URL format
        if not request.repository_url.strip():
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        # Generate session ID upfront
        import uuid
        session_id = str(uuid.uuid4())
        
        # Start the analysis in the background
        background_tasks.add_task(
            run_analysis_workflow,
            session_id,
            request.repository_url,
            request.analysis_period_days,
            request.include_closed_issues
        )
        
        return AnalysisResponse(
            session_id=session_id,
            status="started",
            message="Analysis workflow initiated"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


async def run_analysis_workflow(session_id: str, repository_url: str, analysis_period_days: int, include_closed_issues: bool):
    """Background task to run the analysis workflow."""
    print(f"🚀 Starting analysis workflow for session {session_id}")
    print(f"   Repository: {repository_url}")
    print(f"   Period: {analysis_period_days} days")
    print(f"   Include closed: {include_closed_issues}")
    
    try:
        # Create initial state with the predetermined session_id
        from ..core.state import WorkflowState
        initial_state = WorkflowState(
            repository_url=repository_url,
            analysis_period_days=analysis_period_days,
            include_closed_issues=include_closed_issues
        )
        # Override the auto-generated session_id with our predetermined one
        initial_state.session_id = session_id
        
        # Store the initial state
        active_sessions[session_id] = initial_state
        print(f"✅ Initial state created and stored for session {session_id}")
        
        # Send initial update
        await connection_manager.send_update(session_id, {
            "type": "state_update",
            "session_id": session_id,
            "current_step": "initializing",
            "completion_percentage": 0.0,
            "agent_statuses": {},
            "latest_progress": {"step": "initializing", "message": "Starting analysis workflow...", "timestamp": datetime.now().isoformat()},
            "timestamp": datetime.now().isoformat()
        })
        
        state_count = 0
        async for state in orchestrator.execute_workflow_with_state(initial_state):
            state_count += 1
            print(f"📊 Received state update #{state_count} for session {session_id}")
            print(f"   Current step: {state.current_step}")
            print(f"   Completion: {state.completion_percentage}%")
            
            # Update stored state
            active_sessions[session_id] = state
            
            # Send real-time updates via WebSocket
            latest_progress = state.progress_updates[-1] if state.progress_updates else None
            if latest_progress and 'timestamp' in latest_progress:
                # Convert datetime to string for JSON serialization
                latest_progress = latest_progress.copy()
                if hasattr(latest_progress['timestamp'], 'isoformat'):
                    latest_progress['timestamp'] = latest_progress['timestamp'].isoformat()
            
            await connection_manager.send_update(session_id, {
                "type": "state_update",
                "session_id": session_id,
                "current_step": state.current_step,
                "completion_percentage": state.completion_percentage,
                "agent_statuses": {k: v.value for k, v in state.agent_statuses.items()},
                "latest_progress": latest_progress,
                "timestamp": datetime.now().isoformat()
            })
        
        print(f"✅ Analysis workflow completed for session {session_id} ({state_count} state updates)")
    
    except Exception as e:
        print(f"❌ Error in analysis workflow for session {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if session_id:
            await connection_manager.send_update(session_id, {
                "type": "error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })


@app.get("/status/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get current status of an analysis session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    
    return SessionStatus(
        session_id=session_id,
        current_step=state.current_step,
        completion_percentage=state.completion_percentage,
        agent_statuses={k: v.value for k, v in state.agent_statuses.items()},
        latest_update=state.progress_updates[-1] if state.progress_updates else None
    )


@app.get("/results/{session_id}")
async def get_analysis_results(session_id: str):
    """Get complete analysis results for a session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    
    if state.completion_percentage < 100:
        return {
            "session_id": session_id,
            "status": "in_progress",
            "completion_percentage": state.completion_percentage,
            "current_step": state.current_step
        }
    
    return {
        "session_id": session_id,
        "status": "completed",
        "completion_percentage": state.completion_percentage,
        "repository": state.repository_url,
        "analysis_period_days": state.analysis_period_days,
        "total_issues_analyzed": len(state.raw_issues),
        "final_report": state.final_report,
        "insights": state.insights,
        "recommendations": state.recommendations,
        "agent_statuses": {k: v.value for k, v in state.agent_statuses.items()},
        "routing_decisions": state.routing_decisions,
        "generated_at": state.updated_at.isoformat()
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket, session_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong, requests, etc.)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Echo back for ping/pong
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_text(json.dumps({
                    "type": "keepalive",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        connection_manager.disconnect(session_id)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "orchestrator_initialized": orchestrator is not None,
        "demo_mode": orchestrator.demo_mode if orchestrator else False,
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Simple demo page for testing the API."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GitHub Issue Trend Analyzer - Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 10px; margin-bottom: 10px; }
            button { background: #007bff; color: white; padding: 12px 24px; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .status { margin: 20px 0; padding: 10px; border-left: 4px solid #007bff; background: #f8f9fa; }
            .progress { background: #e9ecef; height: 20px; margin: 10px 0; }
            .progress-bar { height: 100%; background: #007bff; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GitHub Issue Trend Analyzer</h1>
            <p>Multi-agent system for analyzing GitHub repository issue trends.</p>
            
            <form id="analysisForm">
                <div class="form-group">
                    <label for="repo">Repository URL:</label>
                    <input type="text" id="repo" placeholder="e.g., microsoft/vscode or https://github.com/microsoft/vscode" required>
                </div>
                
                <div class="form-group">
                    <label for="days">Analysis Period (days):</label>
                    <input type="number" id="days" value="90" min="1" max="365">
                </div>
                
                <div class="form-group">
                    <label for="closed">Include Closed Issues:</label>
                    <select id="closed">
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                    </select>
                </div>
                
                <button type="submit">Start Analysis</button>
            </form>
            
            <div id="status" class="status" style="display: none;">
                <h3>Analysis Status</h3>
                <div id="progress" class="progress">
                    <div id="progressBar" class="progress-bar" style="width: 0%;"></div>
                </div>
                <p id="statusText">Initializing...</p>
                <p><strong>Session ID:</strong> <span id="sessionId"></span></p>
            </div>
            
            <div id="results" style="display: none;">
                <h3>Results</h3>
                <pre id="resultsText"></pre>
            </div>
        </div>
        
        <script>
            const form = document.getElementById('analysisForm');
            const statusDiv = document.getElementById('status');
            const resultsDiv = document.getElementById('results');
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const repo = document.getElementById('repo').value;
                const days = parseInt(document.getElementById('days').value);
                const closed = document.getElementById('closed').value === 'true';
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            repository_url: repo,
                            analysis_period_days: days,
                            include_closed_issues: closed
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        statusDiv.style.display = 'block';
                        document.getElementById('sessionId').textContent = data.session_id;
                        // In a real implementation, you'd connect to WebSocket here
                        pollStatus(data.session_id);
                    } else {
                        alert('Error: ' + data.detail);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            });
            
            async function pollStatus(sessionId) {
                try {
                    const response = await fetch(`/status/${sessionId}`);
                    const data = await response.json();
                    
                    document.getElementById('statusText').textContent = 
                        `Step: ${data.current_step} (${data.completion_percentage.toFixed(1)}%)`;
                    document.getElementById('progressBar').style.width = data.completion_percentage + '%';
                    
                    if (data.completion_percentage < 100) {
                        setTimeout(() => pollStatus(sessionId), 2000);
                    } else {
                        showResults(sessionId);
                    }
                } catch (error) {
                    console.error('Error polling status:', error);
                }
            }
            
            async function showResults(sessionId) {
                try {
                    const response = await fetch(`/results/${sessionId}`);
                    const data = await response.json();
                    
                    resultsDiv.style.display = 'block';
                    document.getElementById('resultsText').textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    console.error('Error fetching results:', error);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
