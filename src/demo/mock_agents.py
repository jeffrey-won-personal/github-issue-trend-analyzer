"""
Mock agent implementations for demo mode.
These agents simulate the behavior of real agents without requiring API keys.
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

from ..core.state import WorkflowState, AgentStatus, AnalysisQuality, TrendAnalysis
from .mock_data_generator import demo_generator


class MockDataRetrievalAgent:
    """Mock data retrieval agent for demo mode."""
    
    def __init__(self, llm=None):
        self.agent_id = "data_retrieval_agent"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute mock data retrieval."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("data_retrieval", 10.0, "Simulating GitHub API data retrieval...")
        
        try:
            # Simulate API delay
            await asyncio.sleep(1)
            
            # Generate mock repository metadata
            repo_metadata = demo_generator.generate_repository_metadata(state.repository_url)
            state.processed_data["repository_metadata"] = repo_metadata
            
            state.update_progress("data_retrieval", 40.0, f"Retrieved repository: {repo_metadata['full_name']}")
            await asyncio.sleep(0.5)
            
            # Generate mock issues
            state.update_progress("data_retrieval", 60.0, "Generating realistic issue data...")
            mock_issues = demo_generator.generate_issues(
                state.repository_url, 
                state.analysis_period_days,
                state.include_closed_issues
            )
            
            state.raw_issues = mock_issues
            await asyncio.sleep(0.5)
            
            # Assess data quality
            state.update_progress("data_retrieval", 80.0, "Assessing data quality...")
            
            # Determine quality based on number of issues
            if len(mock_issues) >= 100:
                quality = AnalysisQuality.EXCELLENT
            elif len(mock_issues) >= 50:
                quality = AnalysisQuality.GOOD
            elif len(mock_issues) >= 20:
                quality = AnalysisQuality.POOR
            else:
                quality = AnalysisQuality.INSUFFICIENT
            
            state.data_quality = quality
            
            # Add some insights about the retrieval
            state.add_insight(
                self.agent_id,
                "data_retrieval_success",
                f"Successfully retrieved {len(mock_issues)} issues from {repo_metadata['full_name']}. "
                f"Repository has {repo_metadata['stars']} stars and is primarily written in {repo_metadata['language']}.",
                confidence=0.9
            )
            
            state.update_progress("data_retrieval", 100.0, f"Retrieved {len(mock_issues)} issues successfully")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "issues_count": len(mock_issues),
                "data_quality": quality.value,
                "repository": repo_metadata["full_name"]
            })
            
        except Exception as e:
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=str(e))
        
        return state


class MockAnalysisAgent:
    """Mock time-series analysis agent for demo mode."""
    
    def __init__(self, llm=None):
        self.agent_id = "analysis_agent"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute mock time-series analysis."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("analysis", 10.0, "Starting statistical trend analysis...")
        
        try:
            issues = state.raw_issues
            if not issues:
                state.update_agent_status(self.agent_id, AgentStatus.FAILED, error="No issues data available")
                return state
            
            await asyncio.sleep(1)
            
            # Mock trend analysis
            state.update_progress("analysis", 30.0, "Analyzing issue creation trends...")
            
            # Calculate basic statistics
            total_issues = len(issues)
            open_issues = len([i for i in issues if i.state == "open"])
            
            # Mock trend calculation
            recent_issues = len([i for i in issues if (datetime.now() - i.created_at).days <= 30])
            older_issues = len([i for i in issues if (datetime.now() - i.created_at).days > 30])
            
            if older_issues > 0:
                trend_slope = (recent_issues / 30) - (older_issues / max(1, state.analysis_period_days - 30))
            else:
                trend_slope = recent_issues / 30
            
            # Determine trend direction
            if trend_slope > 0.1:
                trend_direction = "increasing"
            elif trend_slope < -0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            await asyncio.sleep(0.5)
            
            # Mock seasonal analysis
            state.update_progress("analysis", 50.0, "Detecting seasonal patterns...")
            
            # Generate mock seasonal patterns
            weekday_pattern = {
                "Monday": random.randint(8, 15),
                "Tuesday": random.randint(10, 18),
                "Wednesday": random.randint(12, 20),
                "Thursday": random.randint(11, 17),
                "Friday": random.randint(6, 12),
                "Saturday": random.randint(2, 8),
                "Sunday": random.randint(1, 6)
            }
            
            await asyncio.sleep(0.5)
            
            # Mock anomaly detection
            state.update_progress("analysis", 70.0, "Detecting anomalies...")
            
            anomalies = []
            if random.random() < 0.7:  # 70% chance of anomalies
                num_anomalies = random.randint(1, 3)
                for i in range(num_anomalies):
                    anomaly_date = datetime.now() - timedelta(days=random.randint(1, state.analysis_period_days))
                    anomalies.append({
                        "date": anomaly_date.strftime("%Y-%m-%d"),
                        "type": random.choice(["high_activity", "unusual_pattern", "burst_activity"]),
                        "value": random.randint(15, 50),
                        "expected": random.randint(3, 12),
                        "severity": random.choice(["medium", "high"])
                    })
            
            await asyncio.sleep(0.5)
            
            # Mock forecasting
            state.update_progress("analysis", 90.0, "Generating forecasts...")
            
            forecast_dates = []
            forecast_values = []
            base_value = recent_issues / 30 if recent_issues > 0 else 3
            
            for i in range(7):
                future_date = datetime.now() + timedelta(days=i+1)
                forecast_dates.append(future_date.strftime("%Y-%m-%d"))
                # Add some trend and randomness
                forecast_value = max(0, base_value + trend_slope * i + random.uniform(-1, 1))
                forecast_values.append(round(forecast_value, 1))
            
            forecast = {
                "linear_forecast": {
                    "method": "linear_regression",
                    "dates": forecast_dates,
                    "values": forecast_values,
                    "confidence": "medium"
                },
                "historical_average": float(total_issues / max(1, state.analysis_period_days) * 30),
                "recent_trend": trend_direction
            }
            
            # Create trend analysis object
            confidence_score = 0.8 if total_issues > 50 else 0.6 if total_issues > 20 else 0.4
            
            trend_analysis = TrendAnalysis(
                trend_direction=trend_direction,
                trend_slope=float(trend_slope),
                seasonal_patterns={"weekday": weekday_pattern},
                anomalies=anomalies,
                forecast=forecast,
                confidence_score=confidence_score,
                analysis_period=f"{state.analysis_period_days} days"
            )
            
            state.trend_analysis = trend_analysis
            
            # Add insights
            state.add_insight(
                self.agent_id,
                "trend_analysis",
                f"Issue trend is {trend_direction} with {len(anomalies)} anomalies detected. "
                f"Confidence score: {confidence_score:.2f}",
                confidence=confidence_score
            )
            
            if trend_direction == "increasing":
                state.add_insight(
                    self.agent_id,
                    "trend_warning",
                    "Increasing issue trend detected. Consider allocating additional resources for issue resolution.",
                    confidence=0.8
                )
            
            state.update_progress("analysis", 100.0, "Time-series analysis completed")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "trend_direction": trend_direction,
                "confidence": confidence_score,
                "anomalies_detected": len(anomalies),
                "forecast_available": True
            })
            
        except Exception as e:
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=str(e))
        
        return state


class MockInsightAgent:
    """Mock insight generation agent for demo mode."""
    
    def __init__(self, llm=None):
        self.agent_id = "insight_agent"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute mock insight generation."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("insight_generation", 10.0, "Generating strategic insights...")
        
        try:
            await asyncio.sleep(1)
            
            issues = state.raw_issues
            trend_analysis = state.trend_analysis
            
            # Mock repository health analysis
            state.update_progress("insight_generation", 25.0, "Analyzing repository health...")
            
            total_issues = len(issues)
            open_issues = len([i for i in issues if i.state == "open"])
            open_ratio = open_issues / total_issues if total_issues > 0 else 0
            
            # Calculate health score
            health_score = 10
            if open_ratio > 0.7:
                health_score -= 3
            if trend_analysis and trend_analysis.trend_direction == "increasing":
                health_score -= 2
            if len([i for i in issues if any("critical" in label.lower() for label in i.labels)]) > 5:
                health_score -= 2
            
            health_score = max(1, health_score)
            
            await asyncio.sleep(0.5)
            
            # Mock maintenance analysis
            state.update_progress("insight_generation", 40.0, "Identifying maintenance patterns...")
            
            bug_issues = [i for i in issues if any("bug" in label.lower() for label in i.labels)]
            maintenance_ratio = len(bug_issues) / total_issues if total_issues > 0 else 0
            
            if maintenance_ratio > 0.5:
                load_assessment = "high"
            elif maintenance_ratio > 0.3:
                load_assessment = "medium"
            else:
                load_assessment = "low"
            
            await asyncio.sleep(0.5)
            
            # Mock community analysis
            state.update_progress("insight_generation", 55.0, "Analyzing community engagement...")
            
            unique_authors = len(set(issue.author for issue in issues))
            avg_comments = sum(issue.comments_count for issue in issues) / len(issues) if issues else 0
            
            if avg_comments > 3:
                engagement_level = "high"
                community_health = 8 + random.randint(0, 2)
            elif avg_comments > 1:
                engagement_level = "medium"
                community_health = 5 + random.randint(0, 3)
            else:
                engagement_level = "low"
                community_health = 2 + random.randint(0, 3)
            
            await asyncio.sleep(0.5)
            
            # Mock risk assessment
            state.update_progress("insight_generation", 70.0, "Assessing risks and opportunities...")
            
            risk_factors = []
            if open_ratio > 0.7:
                risk_factors.append("high_open_issue_ratio")
            if trend_analysis and trend_analysis.trend_direction == "increasing":
                risk_factors.append("increasing_issue_trend")
            if avg_comments < 1:
                risk_factors.append("low_community_engagement")
            
            security_issues = [i for i in issues if any("security" in label.lower() for label in i.labels)]
            if security_issues:
                risk_factors.append("security_concerns")
            
            if len(risk_factors) > 2:
                risk_level = "high"
            elif len(risk_factors) > 0:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            await asyncio.sleep(0.5)
            
            # Store mock insights
            mock_insights = {
                "health": {
                    "health_score": health_score,
                    "positive_indicators": [
                        "Active issue tracking",
                        "Good labeling system",
                        "Regular maintenance"
                    ] if health_score > 6 else [],
                    "concerns": [
                        "High open issue ratio",
                        "Increasing issue trend"
                    ] if health_score < 5 else [],
                    "summary": f"Repository shows {'excellent' if health_score > 8 else 'good' if health_score > 6 else 'concerning'} health indicators."
                },
                "maintenance": {
                    "load_assessment": load_assessment,
                    "debt_score": min(10, len([i for i in issues if (datetime.now() - i.created_at).days > 90 and i.state == "open"]) / 5),
                    "recommendations": [
                        "Implement automated issue triage",
                        "Set up regular maintenance schedules",
                        "Improve issue labeling consistency"
                    ],
                    "priority_areas": ["Bug fixes", "Performance improvements", "Documentation updates"]
                },
                "community": {
                    "health_score": community_health,
                    "engagement_level": engagement_level,
                    "diversity_assessment": "good" if unique_authors > total_issues * 0.5 else "needs improvement",
                    "growth_opportunities": [
                        "Improve contributor documentation",
                        "Add community guidelines",
                        "Create mentorship programs"
                    ]
                },
                "strategic": {
                    "priorities": [
                        "Address issue backlog systematically",
                        "Improve community engagement",
                        "Implement better monitoring"
                    ],
                    "roadmap_impact": "Consider issue trends in product planning",
                    "scaling_advice": "Monitor velocity and adjust team size accordingly",
                    "process_improvements": [
                        "Automated issue labeling",
                        "Response time tracking",
                        "Community feedback loops"
                    ]
                },
                "risks": {
                    "overall_risk": risk_level,
                    "top_risks": risk_factors[:3],
                    "opportunities": [
                        "Leverage community expertise",
                        "Implement automation tools",
                        "Improve documentation"
                    ],
                    "recommended_actions": [
                        "Regular issue triage",
                        "Community engagement initiatives",
                        "Process optimization"
                    ]
                }
            }
            
            state.processed_data["ai_insights"] = mock_insights
            
            # Add structured insights to state
            state.add_insight(
                self.agent_id,
                "repository_health",
                f"Repository health score: {health_score}/10. {mock_insights['health']['summary']}",
                confidence=0.8
            )
            
            state.add_insight(
                self.agent_id,
                "maintenance_load",
                f"Maintenance load assessed as {load_assessment}. Bug ratio: {maintenance_ratio:.1%}",
                confidence=0.7
            )
            
            state.add_insight(
                self.agent_id,
                "community_engagement",
                f"Community engagement is {engagement_level} with {unique_authors} unique contributors.",
                confidence=0.7
            )
            
            state.add_insight(
                self.agent_id,
                "risk_assessment",
                f"Overall risk level: {risk_level}. {len(risk_factors)} risk factors identified.",
                confidence=0.9
            )
            
            # Add recommendations
            for rec in mock_insights["strategic"]["priorities"][:3]:
                state.add_recommendation(
                    self.agent_id,
                    rec,
                    priority="high" if risk_level == "high" else "medium",
                    rationale="Based on comprehensive repository analysis"
                )
            
            state.update_progress("insight_generation", 100.0, "Strategic insights generated successfully")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "insights_generated": len(mock_insights),
                "categories_analyzed": list(mock_insights.keys()),
                "risk_level": risk_level
            })
            
        except Exception as e:
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=str(e))
        
        return state


class MockReportAgent:
    """Mock report generation agent for demo mode."""
    
    def __init__(self, llm=None):
        self.agent_id = "report_agent"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute mock report generation."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("report_generation", 10.0, "Generating comprehensive reports...")
        
        try:
            await asyncio.sleep(1)
            
            # Mock report generation
            issues = state.raw_issues
            trend_analysis = state.trend_analysis
            ai_insights = state.processed_data.get("ai_insights", {})
            repo_metadata = state.processed_data.get("repository_metadata", {})
            
            # Generate executive summary
            state.update_progress("report_generation", 25.0, "Creating executive summary...")
            
            executive_summary = {
                "overview": f"Analysis of {repo_metadata.get('full_name', state.repository_url)} reveals {trend_analysis.trend_direction if trend_analysis else 'stable'} issue trends with strategic implications for development planning.",
                "key_findings": [
                    f"Repository contains {len(issues)} issues over {state.analysis_period_days} day period",
                    f"Issue trend is {trend_analysis.trend_direction if trend_analysis else 'stable'} with {trend_analysis.confidence_score:.1%} confidence" if trend_analysis else "Stable issue pattern observed",
                    f"Repository health scored {ai_insights.get('health', {}).get('health_score', 'N/A')}/10",
                    f"Community engagement is {ai_insights.get('community', {}).get('engagement_level', 'moderate')}"
                ],
                "business_impact": "Repository activity patterns indicate the need for strategic resource allocation and process optimization.",
                "recommendations": [
                    "Implement systematic issue triage process",
                    "Enhance community engagement initiatives", 
                    "Establish predictive monitoring for issue trends"
                ],
                "resources_needed": "2-3 hours weekly for issue management and community engagement"
            }
            
            await asyncio.sleep(0.5)
            
            # Generate technical analysis
            state.update_progress("report_generation", 45.0, "Generating technical analysis...")
            
            technical_analysis = {
                "methodology": "Multi-agent analysis using statistical modeling, pattern recognition, and AI-powered insight generation",
                "statistical_analysis": {
                    "trend_direction": trend_analysis.trend_direction if trend_analysis else "stable",
                    "confidence_score": trend_analysis.confidence_score if trend_analysis else 0.7,
                    "anomalies_detected": len(trend_analysis.anomalies) if trend_analysis else 0,
                    "seasonal_patterns": bool(trend_analysis.seasonal_patterns) if trend_analysis else False
                },
                "patterns_identified": [
                    "Weekly cyclical patterns in issue creation",
                    "Clustering of maintenance-related issues",
                    "Community engagement correlation with response times"
                ],
                "technical_recommendations": [
                    "Implement automated issue labeling system",
                    "Set up real-time monitoring dashboards",
                    "Deploy predictive analytics for resource planning"
                ],
                "implementation_guide": "Use CI/CD integration for automated analysis and alerting systems"
            }
            
            await asyncio.sleep(0.5)
            
            # Generate action items
            state.update_progress("report_generation", 65.0, "Compiling action items...")
            
            action_plan = {
                "immediate_actions": [
                    "Review issues older than 90 days",
                    "Implement basic issue labeling strategy",
                    "Set up weekly issue triage meetings"
                ],
                "short_term_actions": [
                    "Deploy automated issue classification",
                    "Establish response time targets",
                    "Create contributor onboarding process"
                ],
                "long_term_actions": [
                    "Implement comprehensive monitoring system",
                    "Develop community engagement strategy",
                    "Create predictive maintenance workflows"
                ],
                "resource_requirements": "Development team: 4-6 hours/week, Community manager: 2-3 hours/week",
                "success_metrics": [
                    "Reduced average issue resolution time",
                    "Increased community participation",
                    "Improved predictive accuracy"
                ]
            }
            
            await asyncio.sleep(0.5)
            
            # Generate dashboard data
            state.update_progress("report_generation", 80.0, "Preparing dashboard data...")
            
            # Create mock time series data
            daily_issues = {}
            monthly_issues = {}
            
            for issue in issues:
                date_str = issue.created_at.strftime("%Y-%m-%d")
                month_str = issue.created_at.strftime("%Y-%m")
                
                daily_issues[date_str] = daily_issues.get(date_str, 0) + 1
                monthly_issues[month_str] = monthly_issues.get(month_str, 0) + 1
            
            # Issue states
            state_counts = {"open": 0, "closed": 0}
            for issue in issues:
                state_counts[issue.state] = state_counts.get(issue.state, 0) + 1
            
            # Top labels
            label_counts = {}
            for issue in issues:
                for label in issue.labels:
                    label_counts[label] = label_counts.get(label, 0) + 1
            
            top_labels = dict(sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            
            dashboard_data = {
                "summary_metrics": {
                    "total_issues": len(issues),
                    "open_issues": state_counts.get("open", 0),
                    "trend_direction": trend_analysis.trend_direction if trend_analysis else "stable",
                    "health_score": ai_insights.get("health", {}).get("health_score", 7),
                    "risk_level": ai_insights.get("risks", {}).get("overall_risk", "medium")
                },
                "time_series": {
                    "daily_issues": daily_issues,
                    "monthly_issues": monthly_issues
                },
                "distributions": {
                    "issue_states": state_counts,
                    "top_labels": top_labels
                },
                "trend_analysis": {
                    "slope": trend_analysis.trend_slope if trend_analysis else 0,
                    "confidence": trend_analysis.confidence_score if trend_analysis else 0.7,
                    "anomalies": len(trend_analysis.anomalies) if trend_analysis else 0
                },
                "forecast": trend_analysis.forecast if trend_analysis else {},
                "generated_at": datetime.now().isoformat()
            }
            
            await asyncio.sleep(0.5)
            
            # Assemble final report
            state.update_progress("report_generation", 90.0, "Assembling final report...")
            
            final_report = {
                "metadata": {
                    "repository": state.repository_url,
                    "analysis_date": datetime.now().isoformat(),
                    "analysis_period_days": state.analysis_period_days,
                    "total_issues_analyzed": len(issues),
                    "session_id": state.session_id,
                    "confidence_score": trend_analysis.confidence_score if trend_analysis else 0.7,
                    "demo_mode": True
                },
                "executive_summary": executive_summary,
                "technical_analysis": technical_analysis,
                "action_plan": action_plan,
                "dashboard_data": dashboard_data,
                "detailed_insights": ai_insights,
                "recommendations": [
                    {
                        "category": rec["agent_id"],
                        "recommendation": rec["recommendation"], 
                        "priority": rec["priority"],
                        "rationale": rec.get("rationale", "")
                    }
                    for rec in state.recommendations
                ],
                "insights": [
                    {
                        "source": insight["agent_id"],
                        "type": insight["type"],
                        "content": insight["content"],
                        "confidence": insight["confidence"]
                    }
                    for insight in state.insights
                ]
            }
            
            state.final_report = final_report
            state.processed_data["all_reports"] = {
                "executive": executive_summary,
                "technical": technical_analysis,
                "actionable": action_plan,
                "dashboard": dashboard_data
            }
            
            state.update_progress("report_generation", 100.0, "Report generation completed")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "reports_generated": ["executive", "technical", "actionable", "dashboard"],
                "final_report_sections": len(final_report),
                "action_items_count": len(action_plan.get("immediate_actions", []))
            })
            
        except Exception as e:
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=str(e))
        
        return state
