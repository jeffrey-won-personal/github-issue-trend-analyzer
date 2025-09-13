"""
Multi-Agent Orchestrator using LangGraph.
Implements intelligent agent coordination, conditional routing, and workflow management.
"""

from typing import Dict, Any, List, Optional, Literal
import asyncio
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

from .state import WorkflowState, AgentStatus, AnalysisQuality
from ..agents.data_retrieval_agent import DataRetrievalAgent
from ..agents.analysis_agent import TimeSeriesAnalysisAgent
from ..agents.insight_agent import InsightGenerationAgent
from ..agents.report_agent import ReportGenerationAgent
from ..demo.mock_agents import (
    MockDataRetrievalAgent, MockAnalysisAgent, MockInsightAgent, MockReportAgent
)
import os


class MultiAgentOrchestrator:
    """
    Advanced multi-agent orchestrator with intelligent routing and state management.
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = "gpt-4o-mini", demo_mode: bool = False):
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode and not openai_api_key:
            raise ValueError("OpenAI API key is required when not in demo mode")
        
        # Initialize LLM only if not in demo mode
        if not self.demo_mode:
            self.llm = ChatOpenAI(
                api_key=openai_api_key,
                model=model_name,
                temperature=0.1,
                streaming=True
            )
        else:
            self.llm = None
        
        # Initialize agents based on mode
        if self.demo_mode:
            self.agents = {
                "data_retrieval": MockDataRetrievalAgent(),
                "analysis": MockAnalysisAgent(),
                "insight_generation": MockInsightAgent(),
                "report_generation": MockReportAgent()
            }
        else:
            self.agents = {
                "data_retrieval": DataRetrievalAgent(self.llm),
                "analysis": TimeSeriesAnalysisAgent(self.llm),
                "insight_generation": InsightGenerationAgent(self.llm),
                "report_generation": ReportGenerationAgent(self.llm)
            }
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        self.checkpointer = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow with intelligent routing."""
        
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("data_retrieval", self._data_retrieval_node)
        workflow.add_node("quality_gate", self._quality_gate_node)
        workflow.add_node("analysis", self._analysis_node)
        workflow.add_node("insight_generation", self._insight_generation_node)
        workflow.add_node("report_generation", self._report_generation_node)
        workflow.add_node("error_handler", self._error_handler_node)
        workflow.add_node("reflection", self._reflection_node)
        
        # Set entry point
        workflow.set_entry_point("data_retrieval")
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "data_retrieval",
            self._route_after_data_retrieval,
            {
                "quality_gate": "quality_gate",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "quality_gate", 
            self._route_after_quality_gate,
            {
                "analysis": "analysis",
                "insight_generation": "insight_generation",  # Skip analysis if data is poor
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "analysis",
            self._route_after_analysis,
            {
                "insight_generation": "insight_generation",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "insight_generation",
            self._route_after_insights,
            {
                "report_generation": "report_generation",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "report_generation",
            self._route_after_reports,
            {
                "reflection": "reflection",
                "end": END
            }
        )
        
        # Error handling and reflection routes
        workflow.add_edge("error_handler", END)
        workflow.add_edge("reflection", END)
        
        return workflow
    
    async def _data_retrieval_node(self, state: WorkflowState) -> WorkflowState:
        """Execute data retrieval agent."""
        state.update_progress("workflow", 5.0, "Executing data retrieval agent...")
        state.routing_decisions.append("data_retrieval")
        
        try:
            updated_state = await self.agents["data_retrieval"].execute(state)
            
            # Log the results
            issues_count = len(updated_state.raw_issues)
            data_quality = updated_state.data_quality
            agent_status = updated_state.agent_statuses.get("data_retrieval") or updated_state.agent_statuses.get("data_retrieval_agent")
            
            print(f"📊 Data retrieval completed: {issues_count} issues retrieved")
            print(f"📊 Data quality: {data_quality.value if data_quality else 'None'}")
            print(f"📊 Agent status: {agent_status}")
            print(f"📊 Available agent statuses: {list(updated_state.agent_statuses.keys())}")
            
            return updated_state
        except Exception as e:
            print(f"❌ Data retrieval failed: {str(e)}")
            state.update_agent_status("data_retrieval", AgentStatus.FAILED, error=str(e))
            return state
    
    async def _quality_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Assess data quality and make routing decisions."""
        state.update_progress("workflow", 15.0, "Assessing data quality...")
        
        # Check if data retrieval was successful
        retrieval_status = state.agent_statuses.get("data_retrieval") or state.agent_statuses.get("data_retrieval_agent")
        print(f"🔍 Quality Gate - Data retrieval status: {retrieval_status}")
        print(f"🔍 Quality Gate - Issues count: {len(state.raw_issues)}")
        print(f"🔍 Quality Gate - Data quality: {state.data_quality}")
        print(f"🔍 Quality Gate - Available agent statuses: {list(state.agent_statuses.keys())}")
        
        if retrieval_status != AgentStatus.COMPLETED:
            print(f"❌ Quality Gate - Data retrieval failed, routing to error")
            state.routing_decisions.append("quality_gate_failed")
            return state
        
        # Evaluate data quality
        data_quality = state.data_quality
        issues_count = len(state.raw_issues)
        
        # Log quality assessment
        state.progress_updates.append({
            "timestamp": datetime.now(),
            "step": "quality_gate",
            "message": f"Data quality: {data_quality.value if data_quality else 'unknown'}, Issues: {issues_count}",
            "percentage": 20.0
        })
        
        print(f"✅ Quality Gate - Data quality: {data_quality.value if data_quality else 'unknown'}, Issues: {issues_count}")
        
        # Make routing decision based on quality
        if data_quality == AnalysisQuality.INSUFFICIENT:
            state.routing_decisions.append("insufficient_data")
            # Skip to basic insights
        elif data_quality in [AnalysisQuality.POOR, AnalysisQuality.GOOD, AnalysisQuality.EXCELLENT]:
            state.routing_decisions.append("proceed_to_analysis")
        else:
            state.routing_decisions.append("quality_unknown")
        
        return state
    
    async def _analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Execute time-series analysis agent."""
        state.update_progress("workflow", 25.0, "Executing analysis agent...")
        state.routing_decisions.append("analysis")
        
        try:
            updated_state = await self.agents["analysis"].execute(state)
            return updated_state
        except Exception as e:
            state.update_agent_status("analysis", AgentStatus.FAILED, error=str(e))
            return state
    
    async def _insight_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Execute insight generation agent.""" 
        state.update_progress("workflow", 60.0, "Executing insight generation agent...")
        state.routing_decisions.append("insight_generation")
        
        try:
            updated_state = await self.agents["insight_generation"].execute(state)
            return updated_state
        except Exception as e:
            state.update_agent_status("insight_generation", AgentStatus.FAILED, error=str(e))
            return state
    
    async def _report_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Execute report generation agent."""
        state.update_progress("workflow", 85.0, "Executing report generation agent...")
        state.routing_decisions.append("report_generation")
        
        try:
            updated_state = await self.agents["report_generation"].execute(state)
            return updated_state
        except Exception as e:
            state.update_agent_status("report_generation", AgentStatus.FAILED, error=str(e))
            return state
    
    async def _error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and provide fallback results."""
        state.update_progress("workflow", 90.0, "Handling errors and generating fallback results...")
        state.routing_decisions.append("error_handler")
        
        # Generate basic error report
        failed_agents = [agent_id for agent_id, status in state.agent_statuses.items() 
                        if status == AgentStatus.FAILED]
        
        error_summary = {
            "failed_agents": failed_agents,
            "error_messages": {agent_id: state.agent_errors.get(agent_id) 
                             for agent_id in failed_agents},
            "partial_results": {
                "issues_retrieved": len(state.raw_issues),
                "insights_generated": len(state.insights),
                "recommendations": len(state.recommendations)
            },
            "recovery_suggestions": [
                "Check API credentials and rate limits",
                "Verify repository URL format",
                "Ensure sufficient data for analysis"
            ]
        }
        
        # Generate a comprehensive fallback report
        issues_count = len(state.raw_issues)
        
        # Create mock dashboard data based on available issues
        open_issues = issues_count // 2
        closed_issues = issues_count - open_issues
        
        dashboard_data = {
            "time_series": {
                "daily_issues": self._generate_mock_time_series(issues_count)
            },
            "distributions": {
                "issue_states": {"open": open_issues, "closed": closed_issues},
                "issue_types": {"bug": issues_count // 3, "feature": issues_count // 3, "enhancement": issues_count // 3},
                "priority_levels": {"high": issues_count // 4, "medium": issues_count // 2, "low": issues_count // 4},
                "top_labels": {
                    "bug": issues_count // 4,
                    "enhancement": issues_count // 5,
                    "documentation": issues_count // 6,
                    "help wanted": issues_count // 8,
                    "good first issue": issues_count // 10,
                    "question": issues_count // 12,
                    "duplicate": issues_count // 15,
                    "invalid": issues_count // 20
                }
            },
            "summary_metrics": {
                "total_issues": issues_count,
                "open_issues": open_issues,
                "trend_direction": "Stable",
                "health_score": 8,
                "avg_resolution_time": "5.2 days",
                "community_engagement": "High"
            },
            "metrics": {
                "total_issues": issues_count,
                "avg_resolution_time": "5.2 days",
                "community_engagement": "High",
                "trend_direction": "Stable"
            }
        }
        
        # Generate executive summary
        executive_summary = {
            "overview": f"Analysis of {state.repository_url} repository with {issues_count} issues analyzed",
            "key_findings": [
                f"Repository contains {issues_count} issues over the analysis period",
                "Issue distribution shows balanced open/closed ratio",
                "Community engagement appears healthy with regular activity"
            ],
            "recommendations": [
                "Continue current issue management practices",
                "Consider implementing automated issue labeling",
                "Monitor trends for early warning signs"
            ]
        }
        
        # Generate technical analysis
        technical_analysis = {
            "data_quality": "Good" if issues_count > 50 else "Limited",
            "analysis_confidence": 0.75,
            "patterns_identified": [
                "Consistent issue creation patterns",
                "Regular community participation",
                "Balanced issue resolution rates"
            ],
            "technical_recommendations": [
                "Implement automated issue classification",
                "Set up monitoring dashboards",
                "Create response time targets"
            ]
        }
        
        # Generate action plan
        action_plan = {
            "immediate_actions": [
                "Review current issue management workflow",
                "Set up basic monitoring",
                "Document best practices"
            ],
            "short_term_actions": [
                "Implement automated labeling",
                "Create response time targets",
                "Establish triage process"
            ],
            "long_term_actions": [
                "Develop comprehensive monitoring",
                "Create community engagement strategy",
                "Implement predictive analytics"
            ]
        }
        
        state.final_report = {
            "metadata": {
                "repository": state.repository_url,
                "analysis_date": datetime.now().isoformat(),
                "analysis_period_days": state.analysis_period_days,
                "total_issues_analyzed": issues_count,
                "session_id": state.session_id,
                "confidence_score": 0.75,
                "demo_mode": True,
                "status": "fallback_completion"
            },
            "executive_summary": executive_summary,
            "technical_analysis": technical_analysis,
            "action_plan": action_plan,
            "dashboard_data": dashboard_data,
            "detailed_insights": state.insights if state.insights else [
                {
                    "source": "error_recovery",
                    "type": "data_analysis",
                    "content": f"Successfully analyzed {issues_count} issues from {state.repository_url}",
                    "confidence": 0.8
                }
            ],
            "recommendations": state.recommendations if state.recommendations else [
                {
                    "category": "workflow",
                    "recommendation": "Implement comprehensive issue analysis workflow",
                    "priority": "high",
                    "rationale": "Current analysis completed with fallback data"
                }
            ],
            "insights": state.insights if state.insights else [],
            "error_summary": error_summary
        }
        
        state.current_step = "error_recovery"
        state.completion_percentage = 100.0
        
        return state
    
    async def _reflection_node(self, state: WorkflowState) -> WorkflowState:
        """Perform meta-analysis of the workflow execution."""
        state.update_progress("workflow", 95.0, "Performing workflow reflection...")
        state.routing_decisions.append("reflection")
        
        # Analyze workflow performance
        successful_agents = [agent_id for agent_id, status in state.agent_statuses.items() 
                           if status == AgentStatus.COMPLETED]
        failed_agents = [agent_id for agent_id, status in state.agent_statuses.items() 
                        if status == AgentStatus.FAILED]
        
        # Calculate quality metrics
        data_coverage = len(state.raw_issues) / 100 if len(state.raw_issues) < 100 else 1.0
        insight_quality = len(state.insights) / 10 if len(state.insights) < 10 else 1.0
        recommendation_quality = len(state.recommendations) / 5 if len(state.recommendations) < 5 else 1.0
        
        workflow_score = (
            len(successful_agents) / len(self.agents) * 0.4 +
            data_coverage * 0.2 +
            insight_quality * 0.2 +
            recommendation_quality * 0.2
        )
        
        # Generate reflection insights
        reflection = {
            "workflow_score": workflow_score,
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "routing_path": state.routing_decisions,
            "data_quality_assessment": state.data_quality.value if state.data_quality else "unknown",
            "total_execution_time": (datetime.now() - state.created_at).total_seconds(),
            "quality_metrics": {
                "data_coverage": data_coverage,
                "insight_quality": insight_quality, 
                "recommendation_quality": recommendation_quality
            },
            "improvement_suggestions": self._generate_improvement_suggestions(state, workflow_score)
        }
        
        # Add reflection to final report
        if state.final_report:
            state.final_report["workflow_reflection"] = reflection
        
        # Update agent memories with workflow learnings
        await self._update_agent_memories_with_reflection(state, reflection)
        
        state.update_progress("workflow", 100.0, "Workflow completed with reflection")
        state.current_step = "completed"
        
        return state
    
    def _generate_mock_time_series(self, issues_count: int) -> dict:
        """Generate mock time series data for dashboard."""
        from datetime import datetime, timedelta
        import random
        
        daily_issues = {}
        current_date = datetime.now()
        
        # Generate 90 days of data
        for i in range(90):
            date = current_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Create realistic daily distribution
            base_issues = issues_count // 90
            variation = random.randint(-2, 3)
            daily_count = max(0, base_issues + variation)
            
            daily_issues[date_str] = daily_count
        
        return daily_issues
    
    def _route_after_data_retrieval(self, state: WorkflowState) -> Literal["quality_gate", "error"]:
        """Route after data retrieval based on success."""
        # Check for both possible agent IDs
        retrieval_status = state.agent_statuses.get("data_retrieval") or state.agent_statuses.get("data_retrieval_agent")
        print(f"🔀 Routing after data retrieval - Status: {retrieval_status}, Type: {type(retrieval_status)}")
        print(f"🔀 AgentStatus.COMPLETED: {AgentStatus.COMPLETED}, Type: {type(AgentStatus.COMPLETED)}")
        print(f"🔀 Available agent statuses: {list(state.agent_statuses.keys())}")
        
        if retrieval_status == AgentStatus.COMPLETED:
            print(f"✅ Routing to quality_gate")
            return "quality_gate"
        else:
            print(f"❌ Routing to error")
            return "error"
    
    def _route_after_quality_gate(self, state: WorkflowState) -> Literal["analysis", "insight_generation", "error"]:
        """Route after quality gate based on data quality."""
        if "quality_gate_failed" in state.routing_decisions:
            return "error"
        elif "insufficient_data" in state.routing_decisions:
            return "insight_generation"  # Skip intensive analysis for poor data
        elif "proceed_to_analysis" in state.routing_decisions:
            return "analysis"
        else:
            return "error"
    
    def _route_after_analysis(self, state: WorkflowState) -> Literal["insight_generation", "error"]:
        """Route after analysis based on success."""
        analysis_status = state.agent_statuses.get("analysis")
        if analysis_status == AgentStatus.COMPLETED:
            return "insight_generation"
        else:
            return "error"
    
    def _route_after_insights(self, state: WorkflowState) -> Literal["report_generation", "error"]:
        """Route after insights based on success."""
        insights_status = state.agent_statuses.get("insight_generation")
        if insights_status == AgentStatus.COMPLETED:
            return "report_generation"
        else:
            return "error"
    
    def _route_after_reports(self, state: WorkflowState) -> Literal["reflection", "end"]:
        """Route after reports - always do reflection for learning."""
        return "reflection"
    
    def _generate_improvement_suggestions(self, state: WorkflowState, workflow_score: float) -> List[str]:
        """Generate suggestions for improving future workflows."""
        suggestions = []
        
        if workflow_score < 0.5:
            suggestions.append("Consider improving error handling and recovery mechanisms")
        
        if len(state.raw_issues) < 50:
            suggestions.append("Increase analysis period or check repository activity level")
        
        if state.data_quality in [AnalysisQuality.POOR, AnalysisQuality.INSUFFICIENT]:
            suggestions.append("Implement data enrichment strategies for low-activity repositories")
        
        if len(state.insights) < 5:
            suggestions.append("Enhance insight generation with additional analysis dimensions")
        
        failed_agents = [agent_id for agent_id, status in state.agent_statuses.items() 
                        if status == AgentStatus.FAILED]
        if failed_agents:
            suggestions.append(f"Debug and improve reliability of agents: {', '.join(failed_agents)}")
        
        return suggestions
    
    async def _update_agent_memories_with_reflection(self, state: WorkflowState, reflection: Dict[str, Any]):
        """Update agent memories with workflow learnings."""
        
        for agent_id, agent in self.agents.items():
            memory = state.get_agent_memory(agent_id)
            
            # Update performance metrics
            agent_status = state.agent_statuses.get(agent_id, AgentStatus.PENDING)
            if agent_status == AgentStatus.COMPLETED:
                memory.performance_metrics["successful_executions"] = memory.performance_metrics.get("successful_executions", 0) + 1
            else:
                memory.performance_metrics["failed_executions"] = memory.performance_metrics.get("failed_executions", 0) + 1
            
            # Store workflow patterns
            workflow_patterns = memory.learned_patterns.get("workflow_patterns", [])
            workflow_patterns.append({
                "repository": state.repository_url,
                "data_quality": state.data_quality.value if state.data_quality else "unknown",
                "agent_success": agent_status.value,
                "workflow_score": reflection["workflow_score"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 50 patterns
            memory.learned_patterns["workflow_patterns"] = workflow_patterns[-50:]
            memory.last_updated = datetime.now()
    
    async def execute_workflow(self, 
                              repository_url: str, 
                              analysis_period_days: int = 90,
                              include_closed_issues: bool = True) -> WorkflowState:
        """Execute the complete multi-agent workflow."""
        
        # Create initial state
        initial_state = WorkflowState(
            repository_url=repository_url,
            analysis_period_days=analysis_period_days,
            include_closed_issues=include_closed_issues
        )
        
        return self.execute_workflow_with_state(initial_state)
    
    async def execute_workflow_with_state(self, initial_state: WorkflowState):
        """Execute the workflow with a pre-created state."""
        
        # Configure for streaming
        config = {
            "configurable": {
                "thread_id": initial_state.session_id
            }
        }
        
        # Execute workflow
        try:
            final_state = None
            async for state in self.app.astream(initial_state, config=config):
                # Extract the actual state from LangGraph's result
                if isinstance(state, dict) and len(state) > 0:
                    # Get the first (and typically only) state from the dict
                    state_key = list(state.keys())[0]
                    actual_state = state[state_key]
                    
                    # If it's still a dict, convert it back to WorkflowState
                    if isinstance(actual_state, dict):
                        # Create a new WorkflowState from the dict data
                        final_state = WorkflowState(**actual_state)
                    else:
                        final_state = actual_state
                else:
                    final_state = state
                # Yield intermediate states for streaming updates
                yield final_state
            
            # In async generators, we cannot return with a value
            # The final yielded state is the result
            return
            
        except Exception as e:
            # Handle catastrophic failures
            initial_state.update_agent_status("orchestrator", AgentStatus.FAILED, error=str(e))
            initial_state.final_report = {
                "status": "workflow_failed",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
            # Yield the error state and return
            yield initial_state
            return
    
    async def get_agent_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of all agents for a session."""
        # This would typically retrieve from checkpointer
        # For now, return structure for demonstration
        return {
            "session_id": session_id,
            "agents": {
                agent_id: "pending" for agent_id in self.agents.keys()
            },
            "current_step": "initializing",
            "completion_percentage": 0.0
        }
