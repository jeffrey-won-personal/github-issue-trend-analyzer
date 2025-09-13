"""
Time-Series Analysis Agent - Specialized in statistical trend analysis.
Implements advanced time-series modeling with forecasting and anomaly detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Statistical modeling imports
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.arima.model import ARIMA
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..core.state import WorkflowState, AgentStatus, TrendAnalysis, GitHubIssue


class TimeSeriesAnalysisAgent:
    """
    Advanced time-series analysis agent for GitHub issues data.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_id = "analysis_agent"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the time-series analysis phase."""
        state.update_agent_status(self.agent_id, AgentStatus.RUNNING)
        state.update_progress("analysis", 10.0, "Starting time-series analysis...")
        
        try:
            issues = state.raw_issues
            if not issues:
                state.update_agent_status(self.agent_id, AgentStatus.FAILED, error="No issues data available")
                return state
            
            # Convert to DataFrame for analysis
            state.update_progress("analysis", 20.0, "Preparing data for analysis...")
            df = self._prepare_dataframe(issues)
            
            # Perform multiple types of analysis
            analyses = {}
            
            # 1. Basic trend analysis
            state.update_progress("analysis", 30.0, "Analyzing basic trends...")
            analyses["basic_trends"] = await self._analyze_basic_trends(df)
            
            # 2. Seasonal patterns
            state.update_progress("analysis", 50.0, "Detecting seasonal patterns...")
            analyses["seasonal"] = await self._analyze_seasonal_patterns(df)
            
            # 3. Anomaly detection
            state.update_progress("analysis", 70.0, "Detecting anomalies...")
            analyses["anomalies"] = await self._detect_anomalies(df)
            
            # 4. Label-based trends
            state.update_progress("analysis", 80.0, "Analyzing trends by issue type...")
            analyses["label_trends"] = await self._analyze_label_trends(df, issues)
            
            # 5. Forecasting
            state.update_progress("analysis", 90.0, "Generating forecasts...")
            analyses["forecast"] = await self._generate_forecast(df)
            
            # Create comprehensive trend analysis
            trend_analysis = await self._synthesize_analysis(analyses, df)
            state.trend_analysis = trend_analysis
            
            # Generate insights
            await self._generate_analysis_insights(state, analyses, df)
            
            state.update_progress("analysis", 100.0, "Time-series analysis completed")
            state.update_agent_status(self.agent_id, AgentStatus.COMPLETED, output={
                "trend_direction": trend_analysis.trend_direction,
                "confidence": trend_analysis.confidence_score,
                "anomalies_detected": len(trend_analysis.anomalies),
                "forecast_available": bool(trend_analysis.forecast)
            })
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            state.update_agent_status(self.agent_id, AgentStatus.FAILED, error=error_msg)
        
        return state
    
    def _prepare_dataframe(self, issues: List[GitHubIssue]) -> pd.DataFrame:
        """Convert issues to pandas DataFrame for analysis."""
        data = []
        for issue in issues:
            data.append({
                'created_at': issue.created_at,
                'updated_at': issue.updated_at,
                'closed_at': issue.closed_at,
                'state': issue.state,
                'labels': issue.labels,
                'comments_count': issue.comments_count,
                'author': issue.author,
                'number': issue.number
            })
        
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['updated_at'] = pd.to_datetime(df['updated_at'])
        df['closed_at'] = pd.to_datetime(df['closed_at'])
        
        return df.sort_values('created_at')
    
    async def _analyze_basic_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze basic trends in issue creation and closure."""
        try:
            # Daily issue creation
            daily_created = df.groupby(df['created_at'].dt.date).size()
            
            # Daily issue closure (for closed issues)
            closed_issues = df.dropna(subset=['closed_at'])
            daily_closed = closed_issues.groupby(closed_issues['closed_at'].dt.date).size() if len(closed_issues) > 0 else pd.Series()
            
            # Calculate trends
            if len(daily_created) > 1:
                creation_slope = np.polyfit(range(len(daily_created)), daily_created.values, 1)[0]
            else:
                creation_slope = 0
            
            if len(daily_closed) > 1:
                closure_slope = np.polyfit(range(len(daily_closed)), daily_closed.values, 1)[0]
            else:
                closure_slope = 0
            
            # Recent vs older periods comparison
            mid_point = len(daily_created) // 2
            if mid_point > 0:
                recent_avg = daily_created.iloc[mid_point:].mean()
                older_avg = daily_created.iloc[:mid_point].mean()
                relative_change = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
            else:
                relative_change = 0
            
            return {
                "creation_slope": float(creation_slope),
                "closure_slope": float(closure_slope),
                "relative_change_percent": float(relative_change),
                "daily_creation_avg": float(daily_created.mean()),
                "daily_closure_avg": float(daily_closed.mean()) if len(daily_closed) > 0 else 0,
                "creation_volatility": float(daily_created.std()),
                "trend_direction": "increasing" if creation_slope > 0.1 else "decreasing" if creation_slope < -0.1 else "stable"
            }
            
        except Exception as e:
            return {"error": str(e), "trend_direction": "unknown"}
    
    async def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect seasonal patterns in issue activity."""
        try:
            if len(df) < 14:  # Need at least 2 weeks for meaningful seasonal analysis
                return {"message": "Insufficient data for seasonal analysis"}
            
            # Create daily time series
            daily_issues = df.groupby(df['created_at'].dt.date).size()
            daily_issues.index = pd.to_datetime(daily_issues.index)
            
            # Fill missing dates with 0
            full_range = pd.date_range(start=daily_issues.index.min(), end=daily_issues.index.max(), freq='D')
            daily_issues = daily_issues.reindex(full_range, fill_value=0)
            
            patterns = {}
            
            # Day of week patterns
            df['weekday'] = df['created_at'].dt.day_name()
            weekday_avg = df.groupby('weekday').size()
            patterns["weekday"] = weekday_avg.to_dict()
            
            # Hour patterns (if we have enough recent data)
            recent_df = df[df['created_at'] >= (datetime.now() - timedelta(days=30))]
            if len(recent_df) > 0:
                hour_avg = recent_df.groupby(recent_df['created_at'].dt.hour).size()
                patterns["hourly"] = hour_avg.to_dict()
            
            # Monthly patterns
            if len(df) >= 60:  # At least 2 months
                monthly_avg = df.groupby(df['created_at'].dt.month).size()
                patterns["monthly"] = monthly_avg.to_dict()
            
            # Advanced seasonal decomposition if statsmodels is available
            if STATS_AVAILABLE and len(daily_issues) >= 14:
                try:
                    # Use a period of 7 for weekly seasonality
                    decomposition = seasonal_decompose(daily_issues, model='additive', period=7)
                    patterns["seasonal_strength"] = float(decomposition.seasonal.std() / daily_issues.std())
                except:
                    patterns["seasonal_strength"] = 0
            
            return patterns
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in issue patterns."""
        anomalies = []
        
        try:
            # Daily issue counts
            daily_issues = df.groupby(df['created_at'].dt.date).size()
            
            if len(daily_issues) < 7:
                return []
            
            # Simple statistical anomaly detection
            mean_issues = daily_issues.mean()
            std_issues = daily_issues.std()
            threshold = mean_issues + 2 * std_issues
            
            for date, count in daily_issues.items():
                if count > threshold:
                    anomalies.append({
                        "date": date.isoformat(),
                        "type": "high_activity",
                        "value": int(count),
                        "expected": float(mean_issues),
                        "severity": "high" if count > mean_issues + 3 * std_issues else "medium"
                    })
            
            # Advanced anomaly detection if sklearn is available
            if STATS_AVAILABLE and len(daily_issues) >= 10:
                try:
                    # Prepare features for isolation forest
                    features = []
                    for i, (date, count) in enumerate(daily_issues.items()):
                        features.append([
                            count,
                            pd.to_datetime(date).weekday(),
                            pd.to_datetime(date).day,
                            i  # Time index
                        ])
                    
                    features_array = np.array(features)
                    scaler = StandardScaler()
                    features_scaled = scaler.fit_transform(features_array)
                    
                    # Isolation Forest
                    isolation_forest = IsolationForest(contamination=0.1, random_state=42)
                    outliers = isolation_forest.fit_predict(features_scaled)
                    
                    for i, (date, count) in enumerate(daily_issues.items()):
                        if outliers[i] == -1:  # Anomaly detected
                            anomalies.append({
                                "date": date.isoformat(),
                                "type": "statistical_anomaly",
                                "value": int(count),
                                "detection_method": "isolation_forest",
                                "severity": "medium"
                            })
                except Exception as e:
                    print(f"Advanced anomaly detection failed: {e}")
            
            return anomalies
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def _analyze_label_trends(self, df: pd.DataFrame, issues: List[GitHubIssue]) -> Dict[str, Any]:
        """Analyze trends by issue labels."""
        try:
            # Get all unique labels
            all_labels = set()
            for issue in issues:
                all_labels.update(issue.labels)
            
            if not all_labels:
                return {"message": "No labels found in issues"}
            
            label_trends = {}
            
            for label in all_labels:
                # Get issues with this label
                label_issues = [issue for issue in issues if label in issue.labels]
                
                if len(label_issues) < 2:
                    continue
                
                # Create time series for this label
                label_df = pd.DataFrame([{
                    'created_at': issue.created_at,
                    'state': issue.state
                } for issue in label_issues])
                
                label_df['created_at'] = pd.to_datetime(label_df['created_at'])
                daily_counts = label_df.groupby(label_df['created_at'].dt.date).size()
                
                # Calculate trend
                if len(daily_counts) > 1:
                    slope = np.polyfit(range(len(daily_counts)), daily_counts.values, 1)[0]
                    direction = "increasing" if slope > 0.05 else "decreasing" if slope < -0.05 else "stable"
                else:
                    slope = 0
                    direction = "stable"
                
                label_trends[label] = {
                    "total_count": len(label_issues),
                    "slope": float(slope),
                    "direction": direction,
                    "recent_activity": len([i for i in label_issues if (datetime.now() - i.created_at).days <= 7])
                }
            
            # Sort by total count to identify most important labels
            sorted_labels = sorted(label_trends.items(), key=lambda x: x[1]["total_count"], reverse=True)
            
            return {
                "label_trends": dict(sorted_labels[:10]),  # Top 10 labels
                "most_active_labels": [label for label, data in sorted_labels[:5]],
                "trending_up": [label for label, data in sorted_labels if data["direction"] == "increasing"],
                "trending_down": [label for label, data in sorted_labels if data["direction"] == "decreasing"]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_forecast(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate forecast for future issue activity."""
        try:
            daily_issues = df.groupby(df['created_at'].dt.date).size()
            
            if len(daily_issues) < 7:
                return {"message": "Insufficient data for forecasting"}
            
            # Simple linear forecast
            days = range(len(daily_issues))
            slope, intercept = np.polyfit(days, daily_issues.values, 1)
            
            # Forecast next 7 days
            future_days = range(len(daily_issues), len(daily_issues) + 7)
            linear_forecast = [slope * day + intercept for day in future_days]
            
            forecast_dates = []
            last_date = pd.to_datetime(daily_issues.index[-1])
            for i in range(1, 8):
                forecast_dates.append((last_date + timedelta(days=i)).strftime('%Y-%m-%d'))
            
            simple_forecast = {
                "method": "linear_regression",
                "dates": forecast_dates,
                "values": [max(0, round(val, 1)) for val in linear_forecast],
                "confidence": "low" if abs(slope) < 0.1 else "medium"
            }
            
            # Advanced ARIMA forecast if available
            arima_forecast = None
            if STATS_AVAILABLE and len(daily_issues) >= 14:
                try:
                    # Simple ARIMA model
                    model = ARIMA(daily_issues.values, order=(1, 1, 1))
                    fitted_model = model.fit()
                    arima_pred = fitted_model.forecast(steps=7)
                    
                    arima_forecast = {
                        "method": "arima",
                        "dates": forecast_dates,
                        "values": [max(0, round(val, 1)) for val in arima_pred],
                        "confidence": "high"
                    }
                except Exception as e:
                    print(f"ARIMA forecast failed: {e}")
            
            return {
                "linear_forecast": simple_forecast,
                "arima_forecast": arima_forecast,
                "historical_average": float(daily_issues.mean()),
                "recent_trend": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _synthesize_analysis(self, analyses: Dict[str, Any], df: pd.DataFrame) -> TrendAnalysis:
        """Synthesize all analyses into a comprehensive TrendAnalysis object."""
        
        # Determine overall trend direction
        basic_trends = analyses.get("basic_trends", {})
        trend_direction = basic_trends.get("trend_direction", "unknown")
        slope = basic_trends.get("creation_slope", 0)
        
        # Calculate confidence score
        confidence_factors = []
        
        # Factor 1: Data volume
        data_volume_score = min(1.0, len(df) / 100)  # More data = higher confidence
        confidence_factors.append(data_volume_score)
        
        # Factor 2: Trend consistency
        volatility = basic_trends.get("creation_volatility", float('inf'))
        avg_daily = basic_trends.get("daily_creation_avg", 1)
        volatility_score = max(0, 1 - (volatility / avg_daily)) if avg_daily > 0 else 0
        confidence_factors.append(volatility_score)
        
        # Factor 3: Time span
        time_span_days = (df['created_at'].max() - df['created_at'].min()).days
        time_span_score = min(1.0, time_span_days / 90)  # 90 days = full confidence
        confidence_factors.append(time_span_score)
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_slope=float(slope),
            seasonal_patterns=analyses.get("seasonal", {}),
            anomalies=analyses.get("anomalies", []),
            forecast=analyses.get("forecast", {}),
            confidence_score=float(overall_confidence),
            analysis_period=f"{time_span_days} days"
        )
    
    async def _generate_analysis_insights(self, state: WorkflowState, analyses: Dict[str, Any], df: pd.DataFrame):
        """Generate insights from the analysis results."""
        
        # Trend insights
        basic_trends = analyses.get("basic_trends", {})
        if basic_trends:
            slope = basic_trends.get("creation_slope", 0)
            if slope > 0.5:
                state.add_insight(
                    self.agent_id,
                    "trend_alert",
                    f"Strong upward trend detected: +{slope:.2f} issues per day. "
                    "Repository may need additional maintenance resources.",
                    confidence=0.8
                )
            elif slope < -0.5:
                state.add_insight(
                    self.agent_id,
                    "trend_positive",
                    f"Positive downward trend: {slope:.2f} issues per day. "
                    "Repository maintenance appears to be improving.",
                    confidence=0.8
                )
        
        # Seasonal insights
        seasonal = analyses.get("seasonal", {})
        if "weekday" in seasonal:
            weekday_data = seasonal["weekday"]
            if weekday_data:
                max_day = max(weekday_data.keys(), key=lambda k: weekday_data[k])
                min_day = min(weekday_data.keys(), key=lambda k: weekday_data[k])
                
                state.add_insight(
                    self.agent_id,
                    "seasonal_pattern",
                    f"Peak issue activity on {max_day} ({weekday_data[max_day]} issues), "
                    f"lowest on {min_day} ({weekday_data[min_day]} issues). "
                    "Consider adjusting monitoring schedules accordingly.",
                    confidence=0.7
                )
        
        # Anomaly insights
        anomalies = analyses.get("anomalies", [])
        high_severity_anomalies = [a for a in anomalies if a.get("severity") == "high"]
        if high_severity_anomalies:
            state.add_insight(
                self.agent_id,
                "anomaly_alert",
                f"Detected {len(high_severity_anomalies)} high-severity activity spikes. "
                "These may indicate critical issues or release-related activity.",
                confidence=0.9
            )
        
        # Label trends insights
        label_trends = analyses.get("label_trends", {})
        trending_up = label_trends.get("trending_up", [])
        if trending_up:
            state.add_insight(
                self.agent_id,
                "category_trend",
                f"Increasing activity in: {', '.join(trending_up[:3])}. "
                "Focus attention on these issue categories.",
                confidence=0.7
            )
