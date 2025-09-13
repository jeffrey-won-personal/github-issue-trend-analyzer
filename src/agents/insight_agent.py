"""
Insight Generation Agent - AI-powered pattern recognition and strategic recommendations.
Uses advanced reasoning to identify actionable insights from trend analysis.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate

from ..core.state import WorkflowState, AgentStatus, GitHubIssue, TrendAnalysis


class InsightGenerationAgent:
    """
    Advanced AI agent that generates strategic insights and recommendations.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_id = "insight_agent"
        self.insight_categories = [
            "maintenance_load",
            "community_health", 
            "technical_debt",
            "user_experience",
            "development_velocity",
            "security_concerns",
            "documentation_gaps",
            "feature_requests"
        ]
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the insight generation phase."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("insight_generation", 10.0, "Generating strategic insights...")
        
        try:
            # Validate we have the required data
            if not state.raw_issues or not state.trend_analysis:
                state.update_agent_status(self.agent_id, AgentStatus.FAILED, 
                                        error="Missing required data for insight generation")
                return state
            
            # Get agent memory for context
            memory = state.get_agent_memory(self.agent_id)
            
            # Generate different types of insights
            insights = {}
            
            # 1. Repository health insights
            state.update_progress("insight_generation", 25.0, "Analyzing repository health...")
            insights["health"] = await self._generate_health_insights(state.raw_issues, state.trend_analysis)
            
            # 2. Maintenance insights
            state.update_progress("insight_generation", 40.0, "Identifying maintenance patterns...")
            insights["maintenance"] = await self._generate_maintenance_insights(state.raw_issues, state.trend_analysis)
            
            # 3. Community insights
            state.update_progress("insight_generation", 55.0, "Analyzing community engagement...")
            insights["community"] = await self._generate_community_insights(state.raw_issues)
            
            # 4. Strategic recommendations
            state.update_progress("insight_generation", 70.0, "Generating strategic recommendations...")
            insights["strategic"] = await self._generate_strategic_insights(state.raw_issues, state.trend_analysis, memory)
            
            # 5. Risk assessment
            state.update_progress("insight_generation", 85.0, "Assessing risks and opportunities...")
            insights["risks"] = await self._assess_risks_and_opportunities(state.raw_issues, state.trend_analysis)
            
            # Store insights in state
            state.processed_data["ai_insights"] = insights
            
            # Convert insights to standardized format for state
            await self._add_structured_insights_to_state(state, insights)
            
            # Update agent memory with insights patterns
            self._update_agent_memory(memory, insights, state.repository_url)
            
            state.update_progress("insight_generation", 100.0, "Strategic insights generated successfully")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "insights_generated": len(insights),
                "categories_analyzed": list(insights.keys()),
                "risk_level": insights.get("risks", {}).get("overall_risk", "unknown")
            })
            
        except Exception as e:
            error_msg = f"Insight generation failed: {str(e)}"
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=error_msg)
        
        return state
    
    async def _generate_health_insights(self, issues: List[GitHubIssue], trend_analysis: TrendAnalysis) -> Dict[str, Any]:
        """Generate insights about repository health."""
        
        total_issues = len(issues)
        open_issues = len([i for i in issues if i.state == "open"])
        
        # Calculate metrics
        open_ratio = open_issues / total_issues if total_issues > 0 else 0
        recent_issues = len([i for i in issues if (datetime.now() - i.created_at).days <= 30])
        avg_comments = sum(i.comments_count for i in issues) / len(issues) if issues else 0
        
        # Use LLM for health assessment
        health_prompt = f"""
        Analyze the repository health based on these metrics:
        
        Issue Metrics:
        - Total Issues: {total_issues}
        - Open Issues: {open_issues} ({open_ratio:.1%})
        - Recent Issues (30 days): {recent_issues}
        - Average Comments per Issue: {avg_comments:.1f}
        - Trend Direction: {trend_analysis.trend_direction}
        - Trend Confidence: {trend_analysis.confidence_score:.2f}
        
        Provide insights about:
        1. Overall repository health (scale 1-10)
        2. Key health indicators (positive and negative)
        3. Comparison to typical healthy repositories
        4. Specific areas of concern
        
        Format as JSON with keys: health_score, positive_indicators, concerns, summary
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a software engineering expert analyzing repository health."),
                HumanMessage(content=health_prompt)
            ])
            
            # Try to parse JSON response
            health_data = json.loads(response.content)
            return health_data
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to rule-based assessment
            health_score = 7
            if open_ratio > 0.8:
                health_score -= 2
            if trend_analysis.trend_direction == "increasing":
                health_score -= 1
            if avg_comments < 1:
                health_score -= 1
                
            return {
                "health_score": max(1, health_score),
                "positive_indicators": ["Active issue tracking"] if total_issues > 10 else [],
                "concerns": ["High open issue ratio"] if open_ratio > 0.7 else [],
                "summary": f"Repository shows {'concerning' if health_score < 5 else 'moderate' if health_score < 7 else 'good'} health indicators.",
                "error": str(e)
            }
    
    async def _generate_maintenance_insights(self, issues: List[GitHubIssue], trend_analysis: TrendAnalysis) -> Dict[str, Any]:
        """Generate insights about maintenance patterns and needs."""
        
        # Identify maintenance-related issues
        maintenance_keywords = ['bug', 'fix', 'error', 'crash', 'broken', 'maintenance', 'update', 'security']
        maintenance_issues = []
        
        for issue in issues:
            issue_text = (issue.title + ' ' + ' '.join(issue.labels)).lower()
            if any(keyword in issue_text for keyword in maintenance_keywords):
                maintenance_issues.append(issue)
        
        # Calculate metrics
        maintenance_ratio = len(maintenance_issues) / len(issues) if issues else 0
        urgent_issues = [i for i in maintenance_issues if any(label.lower() in ['critical', 'urgent', 'high'] for label in i.labels)]
        old_open_issues = [i for i in issues if i.state == "open" and (datetime.now() - i.created_at).days > 90]
        
        maintenance_prompt = f"""
        Analyze maintenance patterns and needs:
        
        Maintenance Metrics:
        - Total Issues: {len(issues)}
        - Maintenance-related Issues: {len(maintenance_issues)} ({maintenance_ratio:.1%})
        - Urgent Maintenance Issues: {len(urgent_issues)}
        - Old Open Issues (>90 days): {len(old_open_issues)}
        - Overall Trend: {trend_analysis.trend_direction}
        
        Recent Maintenance Issues (sample):
        {chr(10).join([f"- {issue.title}" for issue in maintenance_issues[:5]])}
        
        Provide analysis on:
        1. Maintenance load assessment
        2. Technical debt indicators
        3. Resource allocation recommendations
        4. Prioritization strategy
        
        Format as JSON with keys: load_assessment, debt_score, recommendations, priority_areas
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a technical project manager analyzing maintenance needs."),
                HumanMessage(content=maintenance_prompt)
            ])
            
            return json.loads(response.content)
            
        except Exception as e:
            return {
                "load_assessment": "high" if maintenance_ratio > 0.6 else "medium" if maintenance_ratio > 0.3 else "low",
                "debt_score": min(10, len(old_open_issues) / 10),
                "recommendations": ["Address old open issues", "Implement better testing"],
                "priority_areas": ["Bug fixes", "Security updates"],
                "error": str(e)
            }
    
    async def _generate_community_insights(self, issues: List[GitHubIssue]) -> Dict[str, Any]:
        """Generate insights about community engagement and health."""
        
        # Community metrics
        unique_authors = len(set(issue.author for issue in issues))
        total_comments = sum(issue.comments_count for issue in issues)
        highly_engaged_issues = [i for i in issues if i.comments_count > 5]
        
        # Author activity distribution
        author_counts = {}
        for issue in issues:
            author_counts[issue.author] = author_counts.get(issue.author, 0) + 1
        
        # Find power users vs occasional contributors
        sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
        power_users = [author for author, count in sorted_authors[:5] if count > 3]
        
        community_prompt = f"""
        Analyze community engagement and health:
        
        Community Metrics:
        - Unique Contributors: {unique_authors}
        - Total Comments: {total_comments}
        - Highly Engaged Issues (>5 comments): {len(highly_engaged_issues)}
        - Power Users (>3 issues): {len(power_users)}
        - Average Comments per Issue: {total_comments / len(issues) if issues else 0:.1f}
        
        Top Contributors:
        {chr(10).join([f"- {author}: {count} issues" for author, count in sorted_authors[:5]])}
        
        Provide insights on:
        1. Community health score (1-10)
        2. Engagement patterns
        3. Contributor diversity
        4. Community growth opportunities
        
        Format as JSON with keys: health_score, engagement_level, diversity_assessment, growth_opportunities
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a community manager analyzing open source project health."),
                HumanMessage(content=community_prompt)
            ])
            
            return json.loads(response.content)
            
        except Exception as e:
            return {
                "health_score": min(10, unique_authors / 10),
                "engagement_level": "high" if total_comments / len(issues) > 3 else "medium" if total_comments / len(issues) > 1 else "low",
                "diversity_assessment": "good" if unique_authors > len(issues) * 0.5 else "needs improvement",
                "growth_opportunities": ["Improve documentation", "Add contributor guidelines"],
                "error": str(e)
            }
    
    async def _generate_strategic_insights(self, issues: List[GitHubIssue], trend_analysis: TrendAnalysis, memory: Any) -> Dict[str, Any]:
        """Generate high-level strategic insights and recommendations."""
        
        # Analyze issue labels for feature requests vs bugs
        feature_issues = [i for i in issues if any('feature' in label.lower() or 'enhancement' in label.lower() for label in i.labels)]
        bug_issues = [i for i in issues if any('bug' in label.lower() or 'error' in label.lower() for label in i.labels)]
        
        # Recent trends
        recent_issues = [i for i in issues if (datetime.now() - i.created_at).days <= 30]
        growth_rate = len(recent_issues) / 30 * 365 if recent_issues else 0  # Annualized
        
        # Historical context from memory
        historical_patterns = memory.learned_patterns.get("strategic_insights", [])
        
        strategic_prompt = f"""
        Generate strategic insights for repository management:
        
        Strategic Context:
        - Total Issues Analyzed: {len(issues)}
        - Feature Requests: {len(feature_issues)} ({len(feature_issues)/len(issues)*100:.1f}%)
        - Bug Reports: {len(bug_issues)} ({len(bug_issues)/len(issues)*100:.1f}%)
        - Recent Activity (30 days): {len(recent_issues)} issues
        - Annualized Growth Rate: {growth_rate:.1f} issues/year
        - Trend Direction: {trend_analysis.trend_direction}
        - Analysis Confidence: {trend_analysis.confidence_score:.2f}
        
        Anomalies Detected: {len(trend_analysis.anomalies)}
        
        Provide strategic analysis on:
        1. Resource allocation priorities
        2. Product roadmap implications
        3. Team scaling recommendations
        4. Process improvement opportunities
        5. Risk mitigation strategies
        
        Format as JSON with keys: priorities, roadmap_impact, scaling_advice, process_improvements, risk_mitigation
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a senior engineering manager providing strategic guidance."),
                HumanMessage(content=strategic_prompt)
            ])
            
            strategic_data = json.loads(response.content)
            
            # Add context from memory if available
            if historical_patterns:
                strategic_data["historical_context"] = historical_patterns[-3:]  # Last 3 analyses
            
            return strategic_data
            
        except Exception as e:
            return {
                "priorities": ["Address backlog", "Improve issue triage"],
                "roadmap_impact": "Consider feature request backlog in planning",
                "scaling_advice": "Monitor issue velocity trends",
                "process_improvements": ["Implement better labeling", "Automate common responses"],
                "risk_mitigation": ["Regular backlog review", "Community engagement"],
                "error": str(e)
            }
    
    async def _assess_risks_and_opportunities(self, issues: List[GitHubIssue], trend_analysis: TrendAnalysis) -> Dict[str, Any]:
        """Assess risks and opportunities based on the analysis."""
        
        # Risk indicators
        risk_factors = []
        
        # High volume of open issues
        open_issues = len([i for i in issues if i.state == "open"])
        if open_issues > len(issues) * 0.7:
            risk_factors.append("high_open_issue_ratio")
        
        # Increasing trend
        if trend_analysis.trend_direction == "increasing" and trend_analysis.trend_slope > 1:
            risk_factors.append("rapid_issue_growth")
        
        # Low engagement
        avg_comments = sum(i.comments_count for i in issues) / len(issues) if issues else 0
        if avg_comments < 1:
            risk_factors.append("low_community_engagement")
        
        # Security-related issues
        security_issues = [i for i in issues if any('security' in label.lower() or 'vulnerability' in label.lower() for label in i.labels)]
        if security_issues:
            risk_factors.append("security_concerns")
        
        risk_prompt = f"""
        Assess risks and opportunities for this repository:
        
        Risk Indicators:
        - Identified Risk Factors: {', '.join(risk_factors)}
        - Open Issues: {open_issues}/{len(issues)}
        - Trend: {trend_analysis.trend_direction} (slope: {trend_analysis.trend_slope:.2f})
        - Security Issues: {len(security_issues)}
        - Anomalies: {len(trend_analysis.anomalies)}
        - Analysis Confidence: {trend_analysis.confidence_score:.2f}
        
        Provide assessment with:
        1. Overall risk level (low/medium/high)
        2. Top 3 risks with impact assessment
        3. Top 3 opportunities for improvement
        4. Recommended actions
        
        Format as JSON with keys: overall_risk, top_risks, opportunities, recommended_actions
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a risk assessment expert for software projects."),
                HumanMessage(content=risk_prompt)
            ])
            
            return json.loads(response.content)
            
        except Exception as e:
            # Fallback risk assessment
            risk_level = "high" if len(risk_factors) > 2 else "medium" if len(risk_factors) > 0 else "low"
            
            return {
                "overall_risk": risk_level,
                "top_risks": risk_factors[:3],
                "opportunities": ["Improve automation", "Enhance community engagement", "Better documentation"],
                "recommended_actions": ["Regular monitoring", "Process improvements", "Community outreach"],
                "error": str(e)
            }
    
    async def _add_structured_insights_to_state(self, state: WorkflowState, insights: Dict[str, Any]):
        """Add insights to state in structured format."""
        
        # Add health insights
        health = insights.get("health", {})
        if health:
            state.add_insight(
                self.agent_id, 
                "repository_health",
                f"Repository health score: {health.get('health_score', 'unknown')}/10. {health.get('summary', '')}",
                confidence=0.8
            )
        
        # Add maintenance insights
        maintenance = insights.get("maintenance", {})
        if maintenance:
            load = maintenance.get("load_assessment", "unknown")
            state.add_insight(
                self.agent_id,
                "maintenance_load", 
                f"Maintenance load assessed as {load}. Technical debt score: {maintenance.get('debt_score', 'unknown')}",
                confidence=0.7
            )
        
        # Add strategic recommendations
        strategic = insights.get("strategic", {})
        if strategic and "priorities" in strategic:
            for priority in strategic["priorities"][:3]:  # Top 3 priorities
                state.add_recommendation(
                    self.agent_id,
                    priority,
                    priority="high",
                    rationale="Based on strategic analysis of issue trends and patterns"
                )
        
        # Add risk assessment
        risks = insights.get("risks", {})
        if risks:
            overall_risk = risks.get("overall_risk", "unknown")
            state.add_insight(
                self.agent_id,
                "risk_assessment",
                f"Overall risk level: {overall_risk}. Key risks identified in repository management.",
                confidence=0.9
            )
    
    def _update_agent_memory(self, memory: Any, insights: Dict[str, Any], repo_url: str):
        """Update agent memory with insight patterns."""
        
        # Store strategic insights for future reference
        strategic_insights = memory.learned_patterns.get("strategic_insights", [])
        strategic_insights.append({
            "repository": repo_url,
            "timestamp": datetime.now().isoformat(),
            "insights_summary": {
                "health_score": insights.get("health", {}).get("health_score"),
                "maintenance_load": insights.get("maintenance", {}).get("load_assessment"),
                "risk_level": insights.get("risks", {}).get("overall_risk"),
                "community_health": insights.get("community", {}).get("health_score")
            }
        })
        
        # Keep only last 20 analyses
        memory.learned_patterns["strategic_insights"] = strategic_insights[-20:]
        
        # Update performance metrics
        memory.performance_metrics["insights_generated"] = memory.performance_metrics.get("insights_generated", 0) + 1
        memory.last_updated = datetime.now()

