import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Area, AreaChart
} from 'recharts';
import { 
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle, 
  Users, Clock, GitBranch, Download, RefreshCw, Star
} from 'lucide-react';

const DashboardContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  margin: 2rem 0;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const DashboardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const HeaderLeft = styled.div`
  flex: 1;
`;

const HeaderRight = styled.div`
  display: flex;
  gap: 1rem;
`;

const Title = styled.h1`
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 2rem;
  font-weight: 700;
`;

const Subtitle = styled.p`
  margin: 0;
  color: #4a5568;
  font-size: 1rem;
`;

const ActionButton = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'variant',
})`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  
  background: ${props => props.variant === 'primary' 
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : 'white'};
  color: ${props => props.variant === 'primary' ? 'white' : '#4a5568'};
  border: ${props => props.variant === 'primary' ? 'none' : '2px solid #e2e8f0'};
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const MetricCard = styled.div`
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border-left: 4px solid ${props => props.color || '#667eea'};
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
`;


const MetricIcon = styled.div`
  width: 48px;
  height: 48px;
  background: ${props => props.color || '#667eea'}22;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => props.color || '#667eea'};
  margin-bottom: 1rem;
`;

const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.25rem;
`;

const MetricLabel = styled.div`
  color: #4a5568;
  font-size: 0.875rem;
  font-weight: 500;
`;

const MetricChange = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.5rem;
  
  color: ${props => {
    if (props.type === 'positive') return '#38a169';
    if (props.type === 'negative') return '#e53e3e';
    return '#4a5568';
  }};
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
`;

const ChartCard = styled.div`
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
`;

const ChartTitle = styled.h3`
  margin: 0 0 1rem 0;
  color: #2d3748;
  font-size: 1.1rem;
  font-weight: 600;
`;

const InsightsSection = styled.div`
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 2rem;
`;

const InsightItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #f7fafc;
  border-radius: 8px;
  border-left: 4px solid ${props => props.type === 'warning' ? '#f6ad55' : props.type === 'success' ? '#48bb78' : '#667eea'};
`;

const TabContainer = styled.div`
  margin-bottom: 2rem;
`;

const TabList = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
`;

const Tab = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'active',
})`
  padding: 0.75rem 1.5rem;
  border: none;
  background: none;
  color: ${props => props.active ? '#667eea' : '#4a5568'};
  font-weight: ${props => props.active ? '600' : '400'};
  border-bottom: 2px solid ${props => props.active ? '#667eea' : 'transparent'};
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    color: #667eea;
  }
`;

const COLORS = ['#667eea', '#764ba2', '#48bb78', '#f6ad55', '#e53e3e'];

const ResultsDashboard = ({ results, onReset }) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!results || !results.final_report) {
    return (
      <DashboardContainer>
        <Title>No Results Available</Title>
        <Subtitle>The analysis may still be in progress or encountered an error.</Subtitle>
      </DashboardContainer>
    );
  }

  const { final_report, total_issues_analyzed, repository } = results;
  const { dashboard_data, executive_summary, detailed_insights } = final_report;

  // Prepare chart data
  const timeSeriesData = dashboard_data?.time_series?.daily_issues 
    ? Object.entries(dashboard_data.time_series.daily_issues).map(([date, count]) => ({
        date: new Date(date).toLocaleDateString(),
        issues: count
      })) 
    : [];

  const stateData = dashboard_data?.distributions?.issue_states
    ? Object.entries(dashboard_data.distributions.issue_states).map(([state, count]) => ({
        name: state.charAt(0).toUpperCase() + state.slice(1),
        value: count
      }))
    : [];

  const labelData = dashboard_data?.distributions?.top_labels
    ? Object.entries(dashboard_data.distributions.top_labels)
        .slice(0, 8)
        .map(([label, count]) => ({
          label: label.length > 15 ? label.substring(0, 15) + '...' : label,
          count
        }))
    : [];

  const metrics = dashboard_data?.summary_metrics || {};

  const getTrendIcon = (direction) => {
    switch (direction) {
      case 'increasing': return <TrendingUp size={16} />;
      case 'decreasing': return <TrendingDown size={16} />;
      default: return <Clock size={16} />;
    }
  };

  const getTrendType = (direction) => {
    switch (direction) {
      case 'increasing': return 'negative';
      case 'decreasing': return 'positive';
      default: return 'neutral';
    }
  };

  const isDemoMode = final_report?.metadata?.demo_mode || false;

  return (
    <DashboardContainer>
      <DashboardHeader>
        <HeaderLeft>
          <Title>Analysis Results</Title>
          <Subtitle>
            {repository || 'Repository'} • {total_issues_analyzed} issues analyzed
            {isDemoMode && ' • Demo Mode'}
          </Subtitle>
          {isDemoMode && (
            <div style={{
              display: 'inline-block',
              background: 'linear-gradient(135deg, #667eea22 0%, #764ba222 100%)',
              border: '1px solid #667eea',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              color: '#667eea',
              marginTop: '0.5rem'
            }}>
              🎭 This analysis used realistic mock data to demonstrate all system capabilities
            </div>
          )}
        </HeaderLeft>
        <HeaderRight>
          <ActionButton onClick={() => window.print()}>
            <Download size={16} />
            Export Report
          </ActionButton>
          <ActionButton variant="primary" onClick={onReset}>
            <RefreshCw size={16} />
            New Analysis
          </ActionButton>
        </HeaderRight>
      </DashboardHeader>

      <TabContainer>
        <TabList>
          <Tab active={activeTab === 'overview'} onClick={() => setActiveTab('overview')}>
            Overview
          </Tab>
          <Tab active={activeTab === 'trends'} onClick={() => setActiveTab('trends')}>
            Trends
          </Tab>
          <Tab active={activeTab === 'insights'} onClick={() => setActiveTab('insights')}>
            Insights
          </Tab>
          <Tab active={activeTab === 'recommendations'} onClick={() => setActiveTab('recommendations')}>
            Recommendations
          </Tab>
        </TabList>
      </TabContainer>

      {activeTab === 'overview' && (
        <>
          <MetricsGrid>
            <MetricCard color="#667eea">
              <MetricIcon color="#667eea">
                <GitBranch size={24} />
              </MetricIcon>
              <MetricValue>{metrics.total_issues || 0}</MetricValue>
              <MetricLabel>Total Issues</MetricLabel>
            </MetricCard>

            <MetricCard color="#48bb78">
              <MetricIcon color="#48bb78">
                <CheckCircle size={24} />
              </MetricIcon>
              <MetricValue>{metrics.open_issues || 0}</MetricValue>
              <MetricLabel>Open Issues</MetricLabel>
            </MetricCard>

            <MetricCard color="#f6ad55">
              <MetricIcon color="#f6ad55">
                <TrendingUp size={24} />
              </MetricIcon>
              <MetricValue>{metrics.trend_direction || 'Unknown'}</MetricValue>
              <MetricLabel>Trend Direction</MetricLabel>
              <MetricChange type={getTrendType(metrics.trend_direction)}>
                {getTrendIcon(metrics.trend_direction)}
                Trend Analysis
              </MetricChange>
            </MetricCard>

            <MetricCard color="#764ba2">
              <MetricIcon color="#764ba2">
                <Star size={24} />
              </MetricIcon>
              <MetricValue>{metrics.health_score || 'N/A'}/10</MetricValue>
              <MetricLabel>Health Score</MetricLabel>
              <MetricChange type={metrics.health_score > 7 ? 'positive' : metrics.health_score < 4 ? 'negative' : 'neutral'}>
                Repository Health
              </MetricChange>
            </MetricCard>
          </MetricsGrid>

          <ChartsGrid>
            <ChartCard>
              <ChartTitle>Issue Creation Trend</ChartTitle>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="issues" stroke="#667eea" fill="#667eea" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard>
              <ChartTitle>Issue States Distribution</ChartTitle>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stateData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {stateData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </ChartsGrid>
        </>
      )}

      {activeTab === 'trends' && (
        <ChartsGrid>
          <ChartCard style={{ gridColumn: '1 / -1' }}>
            <ChartTitle>Top Issue Labels</ChartTitle>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={labelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </ChartsGrid>
      )}

      {activeTab === 'insights' && (
        <InsightsSection>
          <ChartTitle>AI-Generated Insights</ChartTitle>
          
          {executive_summary?.key_findings?.map((finding, index) => (
            <InsightItem key={index} type="info">
              <CheckCircle size={20} color="#667eea" style={{ marginTop: '0.125rem' }} />
              <div>
                <strong>Key Finding:</strong> {finding}
              </div>
            </InsightItem>
          ))}

          {detailed_insights?.repository_health?.concerns?.map((concern, index) => (
            <InsightItem key={index} type="warning">
              <AlertTriangle size={20} color="#f6ad55" style={{ marginTop: '0.125rem' }} />
              <div>
                <strong>Area of Concern:</strong> {concern}
              </div>
            </InsightItem>
          ))}
        </InsightsSection>
      )}

      {activeTab === 'recommendations' && (
        <InsightsSection>
          <ChartTitle>Strategic Recommendations</ChartTitle>
          
          {executive_summary?.recommendations?.map((rec, index) => (
            <InsightItem key={index} type="success">
              <CheckCircle size={20} color="#48bb78" style={{ marginTop: '0.125rem' }} />
              <div>
                <strong>Recommendation {index + 1}:</strong> {rec}
              </div>
            </InsightItem>
          ))}

          {final_report?.recommendations?.map((rec, index) => (
            <InsightItem key={index} type="info">
              <Users size={20} color="#667eea" style={{ marginTop: '0.125rem' }} />
              <div>
                <strong>{rec.category}:</strong> {rec.recommendation}
                {rec.rationale && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#4a5568' }}>
                    <em>Rationale: {rec.rationale}</em>
                  </div>
                )}
              </div>
            </InsightItem>
          ))}
        </InsightsSection>
      )}
    </DashboardContainer>
  );
};

export default ResultsDashboard;
