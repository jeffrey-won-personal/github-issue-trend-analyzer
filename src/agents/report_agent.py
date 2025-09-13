"""
Report Generation Agent - Creates comprehensive, structured reports.
Synthesizes all analysis results into actionable reports for different audiences.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..core.state import WorkflowState, AgentStatus, TrendAnalysis


class ReportGenerationAgent:
    """
    Advanced report generation agent that creates multiple report formats.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_id = "report_agent"
        self.report_templates = {
            "executive": "executive_summary_template",
            "technical": "technical_analysis_template", 
            "actionable": "action_items_template",
            "dashboard": "dashboard_data_template"
        }
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the report generation phase."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("report_generation", 10.0, "Generating comprehensive reports...")
        
        try:
            # Validate we have the required data
            if not state.trend_analysis or not state.insights:
                state.update_agent_status(self.agent_id, AgentStatus.FAILED, 
                                        error="Missing required data for report generation")
                return state
            
            # Generate multiple report formats
            reports = {}
            
            # 1. Executive Summary
            state.update_progress("report_generation", 25.0, "Creating executive summary...")
            reports["executive"] = await self._generate_executive_summary(state)
            
            # 2. Technical Analysis Report
            state.update_progress("report_generation", 45.0, "Generating technical analysis...")
            reports["technical"] = await self._generate_technical_report(state)
            
            # 3. Action Items Report
            state.update_progress("report_generation", 65.0, "Compiling action items...")
            reports["actionable"] = await self._generate_action_items_report(state)
            
            # 4. Dashboard Data
            state.update_progress("report_generation", 80.0, "Preparing dashboard data...")
            reports["dashboard"] = await self._generate_dashboard_data(state)
            
            # 5. Comprehensive Final Report
            state.update_progress("report_generation", 90.0, "Assembling final report...")
            final_report = await self._generate_final_report(state, reports)
            
            # Store all reports in state
            state.final_report = final_report
            state.processed_data["all_reports"] = reports
            
            # Generate metadata about the reports
            report_metadata = {
                "generated_at": datetime.now().isoformat(),
                "repository": state.repository_url,
                "analysis_period": state.analysis_period_days,
                "total_issues_analyzed": len(state.raw_issues),
                "report_formats": list(reports.keys()),
                "confidence_score": state.trend_analysis.confidence_score if state.trend_analysis else 0
            }
            
            state.processed_data["report_metadata"] = report_metadata
            
            state.update_progress("report_generation", 100.0, "Report generation completed")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "reports_generated": list(reports.keys()),
                "final_report_sections": len(final_report.get("sections", [])),
                "action_items_count": len(reports.get("actionable", {}).get("action_items", []))
            })
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=error_msg)
        
        return state
    
    async def _generate_executive_summary(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate executive summary for leadership."""
        
        trend_analysis = state.trend_analysis
        insights = state.insights
        issues = state.raw_issues
        repo_metadata = state.processed_data.get("repository_metadata", {})
        
        # Prepare summary data
        total_issues = len(issues)
        open_issues = len([i for i in issues if i.state == "open"])
        recent_issues = len([i for i in issues if (datetime.now() - i.created_at).days <= 30])
        
        ai_insights = state.processed_data.get("ai_insights", {})
        health_score = ai_insights.get("health", {}).get("health_score", "unknown")
        risk_level = ai_insights.get("risks", {}).get("overall_risk", "unknown")
        
        exec_prompt = f"""
        Generate an executive summary for repository analysis:
        
        Repository: {repo_metadata.get('full_name', state.repository_url)}
        Analysis Period: {state.analysis_period_days} days
        
        Key Metrics:
        - Total Issues: {total_issues}
        - Open Issues: {open_issues} ({open_issues/total_issues*100:.1f}% if total_issues > 0 else 0)
        - Recent Activity: {recent_issues} issues in last 30 days
        - Trend Direction: {trend_analysis.trend_direction}
        - Health Score: {health_score}/10
        - Risk Level: {risk_level}
        - Repository Stars: {repo_metadata.get('stars', 'N/A')}
        
        Create an executive summary with:
        1. One-sentence overall assessment
        2. Key findings (3-4 bullet points)
        3. Business impact analysis
        4. Top 3 recommendations
        5. Resource requirements
        
        Keep it concise and business-focused. Use clear, non-technical language.
        Format as JSON with keys: overview, key_findings, business_impact, recommendations, resources_needed
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an executive consultant providing strategic technology assessments."),
                HumanMessage(content=exec_prompt)
            ])
            
            return json.loads(response.content)
            
        except Exception as e:
            return {
                "overview": f"Analysis of {repo_metadata.get('full_name', 'repository')} shows {trend_analysis.trend_direction} issue trends.",
                "key_findings": [
                    f"Repository has {total_issues} total issues with {open_issues} currently open",
                    f"Issue trend is {trend_analysis.trend_direction}",
                    f"Health score assessed at {health_score}/10"
                ],
                "business_impact": "Repository health impacts development velocity and user satisfaction.",
                "recommendations": ["Monitor issue trends", "Improve response times", "Enhance documentation"],
                "resources_needed": "Development team attention for issue triage and resolution",
                "error": str(e)
            }
    
    async def _generate_technical_report(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate detailed technical analysis report."""
        
        trend_analysis = state.trend_analysis
        ai_insights = state.processed_data.get("ai_insights", {})
        
        # Extract technical details
        anomalies = trend_analysis.anomalies if trend_analysis else []
        seasonal_patterns = trend_analysis.seasonal_patterns if trend_analysis else {}
        forecast = trend_analysis.forecast if trend_analysis else {}
        
        tech_prompt = f"""
        Generate a detailed technical analysis report:
        
        Trend Analysis:
        - Direction: {trend_analysis.trend_direction if trend_analysis else 'unknown'}
        - Slope: {trend_analysis.trend_slope if trend_analysis else 0}
        - Confidence: {trend_analysis.confidence_score if trend_analysis else 0:.2f}
        - Analysis Period: {trend_analysis.analysis_period if trend_analysis else 'unknown'}
        
        Anomalies Detected: {len(anomalies)}
        Seasonal Patterns: {bool(seasonal_patterns)}
        Forecast Available: {bool(forecast)}
        
        Maintenance Insights:
        {json.dumps(ai_insights.get('maintenance', {}), indent=2)}
        
        Community Insights:
        {json.dumps(ai_insights.get('community', {}), indent=2)}
        
        Create a technical report with:
        1. Methodology explanation
        2. Statistical analysis results
        3. Pattern identification
        4. Technical recommendations
        5. Implementation guidance
        
        Format as JSON with keys: methodology, statistical_analysis, patterns_identified, technical_recommendations, implementation_guide
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a senior data scientist creating technical analysis reports."),
                HumanMessage(content=tech_prompt)
            ])
            
            technical_report = json.loads(response.content)
            
            # Add raw data references
            technical_report["data_summary"] = {
                "total_issues_analyzed": len(state.raw_issues),
                "analysis_confidence": trend_analysis.confidence_score if trend_analysis else 0,
                "anomalies_count": len(anomalies),
                "trend_slope": trend_analysis.trend_slope if trend_analysis else 0
            }
            
            return technical_report
            
        except Exception as e:
            return {
                "methodology": "Time-series analysis of GitHub issues using statistical modeling",
                "statistical_analysis": {
                    "trend_direction": trend_analysis.trend_direction if trend_analysis else "unknown",
                    "confidence_score": trend_analysis.confidence_score if trend_analysis else 0,
                    "anomalies_detected": len(anomalies)
                },
                "patterns_identified": ["Weekly patterns in issue creation", "Maintenance issue clustering"],
                "technical_recommendations": ["Implement automated issue labeling", "Set up monitoring dashboards"],
                "implementation_guide": "Use CI/CD integration for automated analysis",
                "error": str(e)
            }
    
    async def _generate_action_items_report(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate actionable recommendations with priorities."""
        
        recommendations = state.recommendations
        ai_insights = state.processed_data.get("ai_insights", {})
        
        # Extract actionable items from various sources
        action_items = []
        
        # From explicit recommendations
        for rec in recommendations:
            action_items.append({
                "action": rec["recommendation"],
                "priority": rec["priority"],
                "source": f"Agent: {rec['agent_id']}",
                "rationale": rec.get("rationale", ""),
                "category": "general"
            })
        
        # From strategic insights
        strategic = ai_insights.get("strategic", {})
        if strategic and "recommended_actions" in strategic:
            for action in strategic["recommended_actions"][:3]:
                action_items.append({
                    "action": action,
                    "priority": "medium",
                    "source": "Strategic Analysis",
                    "rationale": "Derived from strategic pattern analysis",
                    "category": "strategic"
                })
        
        # From risk assessment
        risks = ai_insights.get("risks", {})
        if risks and "recommended_actions" in risks:
            for action in risks["recommended_actions"][:2]:
                action_items.append({
                    "action": action,
                    "priority": "high",
                    "source": "Risk Assessment",
                    "rationale": "Risk mitigation strategy",
                    "category": "risk_mitigation"
                })
        
        action_prompt = f"""
        Create an actionable report from these recommendations:
        
        Action Items Identified:
        {json.dumps(action_items, indent=2)}
        
        Repository Context:
        - Issues Analyzed: {len(state.raw_issues)}
        - Trend: {state.trend_analysis.trend_direction if state.trend_analysis else 'unknown'}
        - Risk Level: {ai_insights.get('risks', {}).get('overall_risk', 'unknown')}
        
        Create structured action plan with:
        1. Immediate actions (next 7 days)
        2. Short-term actions (next 30 days)  
        3. Long-term actions (next 90 days)
        4. Resource requirements for each
        5. Success metrics
        
        Format as JSON with keys: immediate_actions, short_term_actions, long_term_actions, resource_requirements, success_metrics
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a project manager creating actionable implementation plans."),
                HumanMessage(content=action_prompt)
            ])
            
            action_report = json.loads(response.content)
            action_report["all_action_items"] = action_items
            
            return action_report
            
        except Exception as e:
            # Fallback action items
            return {
                "immediate_actions": [
                    "Review open issues older than 90 days",
                    "Implement issue labeling strategy"
                ],
                "short_term_actions": [
                    "Set up automated issue triage",
                    "Establish response time targets"
                ],
                "long_term_actions": [
                    "Implement comprehensive monitoring",
                    "Develop community engagement strategy"
                ],
                "resource_requirements": "2-3 hours per week for issue management",
                "success_metrics": ["Reduced average issue resolution time", "Improved community engagement"],
                "all_action_items": action_items,
                "error": str(e)
            }
    
    async def _generate_dashboard_data(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate data formatted for dashboard visualization."""
        
        issues = state.raw_issues
        trend_analysis = state.trend_analysis
        
        # Prepare time series data
        import pandas as pd
        
        # Daily issue counts
        df = pd.DataFrame([{
            'date': issue.created_at.strftime('%Y-%m-%d'),
            'created': 1,
            'state': issue.state,
            'labels': issue.labels,
            'comments': issue.comments_count
        } for issue in issues])
        
        daily_counts = df.groupby('date').size().to_dict()
        
        # Labels distribution
        all_labels = []
        for issue in issues:
            all_labels.extend(issue.labels)
        
        from collections import Counter
        label_counts = dict(Counter(all_labels).most_common(10))
        
        # State distribution
        state_counts = df['state'].value_counts().to_dict()
        
        # Monthly trends
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
        monthly_counts = df.groupby('month').size().to_dict()
        
        dashboard_data = {
            "summary_metrics": {
                "total_issues": len(issues),
                "open_issues": len([i for i in issues if i.state == "open"]),
                "trend_direction": trend_analysis.trend_direction if trend_analysis else "unknown",
                "health_score": state.processed_data.get("ai_insights", {}).get("health", {}).get("health_score", 0),
                "risk_level": state.processed_data.get("ai_insights", {}).get("risks", {}).get("overall_risk", "unknown")
            },
            "time_series": {
                "daily_issues": daily_counts,
                "monthly_issues": monthly_counts
            },
            "distributions": {
                "issue_states": state_counts,
                "top_labels": label_counts
            },
            "trend_analysis": {
                "slope": trend_analysis.trend_slope if trend_analysis else 0,
                "confidence": trend_analysis.confidence_score if trend_analysis else 0,
                "anomalies": len(trend_analysis.anomalies) if trend_analysis else 0
            },
            "forecast": trend_analysis.forecast if trend_analysis else {},
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard_data
    
    async def _generate_final_report(self, state: WorkflowState, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive final report combining all analyses."""
        
        # Structure the final report
        final_report = {
            "metadata": {
                "repository": state.repository_url,
                "analysis_date": datetime.now().isoformat(),
                "analysis_period_days": state.analysis_period_days,
                "total_issues_analyzed": len(state.raw_issues),
                "session_id": state.session_id,
                "confidence_score": state.trend_analysis.confidence_score if state.trend_analysis else 0
            },
            "executive_summary": reports.get("executive", {}),
            "technical_analysis": reports.get("technical", {}),
            "action_plan": reports.get("actionable", {}),
            "dashboard_data": reports.get("dashboard", {}),
            "detailed_insights": {
                "repository_health": state.processed_data.get("ai_insights", {}).get("health", {}),
                "maintenance_analysis": state.processed_data.get("ai_insights", {}).get("maintenance", {}),
                "community_assessment": state.processed_data.get("ai_insights", {}).get("community", {}),
                "risk_evaluation": state.processed_data.get("ai_insights", {}).get("risks", {})
            },
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
        
        return final_report


