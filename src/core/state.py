"""
Core state management for the multi-agent GitHub Issue Trend Analyzer.
This module defines the shared state structure and state management utilities.
"""

from typing import Dict, List, Optional, Any, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from enum import Enum


class AgentStatus(str, Enum):
    """Status of individual agents during execution."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AnalysisQuality(str, Enum):
    """Quality assessment of retrieved data."""
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    INSUFFICIENT = "insufficient"


class GitHubIssue(BaseModel):
    """Structured representation of a GitHub issue."""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    author: str
    comments_count: int = 0
    reactions_count: int = 0


class TrendAnalysis(BaseModel):
    """Results from time-series trend analysis."""
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_slope: float
    seasonal_patterns: Dict[str, Any] = Field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    forecast: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float
    analysis_period: str


class AgentMemory(BaseModel):
    """Memory system for agents to maintain context."""
    agent_id: str
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    learned_patterns: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)


class WorkflowState(BaseModel):
    """
    Central state for the multi-agent workflow.
    This is passed between agents and maintains the complete context.
    """
    # Workflow metadata
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Input parameters
    repository_url: str
    analysis_period_days: int = 90
    include_closed_issues: bool = True
    
    # Agent status tracking
    agent_statuses: Dict[str, AgentStatus] = Field(default_factory=dict)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    agent_errors: Dict[str, str] = Field(default_factory=dict)
    
    # Data pipeline
    raw_issues: List[GitHubIssue] = Field(default_factory=list)
    processed_data: Dict[str, Any] = Field(default_factory=dict)
    trend_analysis: Optional[TrendAnalysis] = None
    
    # Quality and routing
    data_quality: Optional[AnalysisQuality] = None
    routing_decisions: List[str] = Field(default_factory=list)
    
    # Insights and outputs
    insights: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    final_report: Optional[Dict[str, Any]] = None
    
    # Agent memory and learning
    agent_memories: Dict[str, AgentMemory] = Field(default_factory=dict)
    
    # Streaming and UI updates
    progress_updates: List[Dict[str, Any]] = Field(default_factory=list)
    current_step: str = "initializing"
    completion_percentage: float = 0.0
    
    def update_agent_status(self, agent_id: str, status: AgentStatus, output: Any = None, error: str = None):
        """Update the status of a specific agent."""
        self.agent_statuses[agent_id] = status
        self.updated_at = datetime.now()
        
        if output is not None:
            self.agent_outputs[agent_id] = output
            
        if error is not None:
            self.agent_errors[agent_id] = error
            
        # Add progress update for streaming
        self.progress_updates.append({
            "timestamp": datetime.now(),
            "agent_id": agent_id,
            "status": status.value,
            "message": f"Agent {agent_id} is now {status.value}"
        })
    
    def add_insight(self, agent_id: str, insight_type: str, content: Any, confidence: float = 1.0):
        """Add an insight discovered by an agent."""
        self.insights.append({
            "agent_id": agent_id,
            "type": insight_type,
            "content": content,
            "confidence": confidence,
            "timestamp": datetime.now()
        })
    
    def add_recommendation(self, agent_id: str, recommendation: str, priority: str = "medium", rationale: str = ""):
        """Add a recommendation from an agent."""
        self.recommendations.append({
            "agent_id": agent_id,
            "recommendation": recommendation,
            "priority": priority,
            "rationale": rationale,
            "timestamp": datetime.now()
        })
    
    def update_progress(self, step: str, percentage: float, message: str = ""):
        """Update overall workflow progress."""
        self.current_step = step
        self.completion_percentage = min(100.0, max(0.0, percentage))
        self.progress_updates.append({
            "timestamp": datetime.now(),
            "step": step,
            "percentage": percentage,
            "message": message
        })
    
    def get_agent_memory(self, agent_id: str) -> AgentMemory:
        """Get or create memory for a specific agent."""
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = AgentMemory(agent_id=agent_id)
        return self.agent_memories[agent_id]


# State annotation for LangGraph
def update_state(current: WorkflowState, update: dict) -> WorkflowState:
    """Update state with new information."""
    for key, value in update.items():
        if hasattr(current, key):
            setattr(current, key, value)
    current.updated_at = datetime.now()
    return current


# Type annotation for LangGraph state
StateAnnotation = Annotated[WorkflowState, update_state]

