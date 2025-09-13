import React from 'react';
import styled, { keyframes } from 'styled-components';
import { Clock, CheckCircle, XCircle, Loader, Play } from 'lucide-react';

const pulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`;

const ProgressContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  margin: 2rem 0;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const ProgressHeader = styled.div`
  text-align: center;
  margin-bottom: 2rem;
`;

const ProgressTitle = styled.h2`
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
`;

const ProgressSubtitle = styled.p`
  margin: 0;
  color: #4a5568;
  font-size: 1rem;
`;

const OverallProgress = styled.div`
  margin-bottom: 2rem;
`;

const ProgressBarContainer = styled.div`
  background: #e2e8f0;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 1rem;
`;

const ProgressBar = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'progress',
})`
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  transition: width 0.3s ease;
  width: ${props => props.progress}%;
`;

const ProgressText = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #4a5568;
  font-size: 0.875rem;
`;

const CurrentStep = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #2d3748;
`;

const AgentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
`;

const AgentCard = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'status',
})`
  background: ${props => {
    switch (props.status) {
      case 'completed': return 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
      case 'running': return 'linear-gradient(135deg, #4299e1 0%, #3182ce 100%)';
      case 'failed': return 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
      default: return 'linear-gradient(135deg, #a0aec0 0%, #718096 100%)';
    }
  }};
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  animation: ${props => props.status === 'running' ? pulse : 'none'} 2s infinite;
`;

const AgentHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
`;

const AgentName = styled.h3`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
`;

const AgentStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
`;

const AgentDescription = styled.p`
  margin: 0;
  font-size: 0.875rem;
  opacity: 0.9;
  line-height: 1.4;
`;

const StatusIcon = ({ status }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle size={20} />;
    case 'running':
      return <Loader size={20} className="animate-spin" />;
    case 'failed':
      return <XCircle size={20} />;
    default:
      return <Clock size={20} />;
  }
};

const getAgentDisplayName = (agentId) => {
  const names = {
    'data_retrieval_agent': 'Data Retrieval',
    'analysis_agent': 'Time-Series Analysis',
    'insight_agent': 'Insight Generation',
    'report_agent': 'Report Generation'
  };
  return names[agentId] || agentId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const getAgentDescription = (agentId) => {
  const descriptions = {
    'data_retrieval_agent': 'Fetching GitHub issues and repository metadata with intelligent rate limiting',
    'analysis_agent': 'Performing statistical trend analysis and anomaly detection',
    'insight_agent': 'Generating strategic insights and AI-powered recommendations',
    'report_agent': 'Creating comprehensive reports and actionable summaries'
  };
  return descriptions[agentId] || 'Processing repository data...';
};

const AnalysisProgress = ({ sessionData }) => {
  const {
    completion_percentage = 0,
    current_step = 'Initializing',
    agent_statuses = {},
    latest_progress = null
  } = sessionData || {};

  const agentOrder = ['data_retrieval_agent', 'analysis_agent', 'insight_agent', 'report_agent'];
  
  return (
    <ProgressContainer>
      <ProgressHeader>
        <ProgressTitle>
          <Loader size={24} style={{ animation: 'spin 1s linear infinite' }} />
          Multi-Agent Analysis in Progress
        </ProgressTitle>
        <ProgressSubtitle>
          Our specialized agents are working together to analyze your repository
        </ProgressSubtitle>
      </ProgressHeader>

      <OverallProgress>
        <ProgressBarContainer>
          <ProgressBar progress={completion_percentage} />
        </ProgressBarContainer>
        <ProgressText>
          <CurrentStep>
            <Play size={16} />
            {current_step === 'data_retrieval' && 'Retrieving Repository Data'}
            {current_step === 'workflow' && 'Processing Analysis'}
            {current_step === 'analysis' && 'Running Trend Analysis'}
            {current_step === 'error_recovery' && 'Generating Results'}
            {!['data_retrieval', 'workflow', 'analysis', 'error_recovery'].includes(current_step) && current_step}
          </CurrentStep>
          <span>{Math.round(completion_percentage)}% Complete</span>
        </ProgressText>
      </OverallProgress>

      {latest_progress && (
        <div style={{
          background: '#f7fafc',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          borderLeft: '4px solid #667eea'
        }}>
          <div style={{ color: '#2d3748', fontWeight: '600', marginBottom: '0.25rem' }}>
            Latest Update
          </div>
          <div style={{ color: '#4a5568', fontSize: '0.875rem' }}>
            {latest_progress.message || latest_progress.step}
          </div>
          <div style={{ color: '#718096', fontSize: '0.75rem', marginTop: '0.25rem' }}>
            {new Date(latest_progress.timestamp).toLocaleTimeString()}
          </div>
        </div>
      )}

      <AgentGrid>
        {agentOrder.map(agentId => {
          const status = agent_statuses[agentId] || 'pending';
          
          return (
            <AgentCard key={agentId} status={status}>
              <AgentHeader>
                <AgentName>{getAgentDisplayName(agentId)}</AgentName>
                <AgentStatus>
                  <StatusIcon status={status} />
                </AgentStatus>
              </AgentHeader>
              <AgentDescription>
                {getAgentDescription(agentId)}
              </AgentDescription>
              
              {status === 'running' && (
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: '3px',
                  background: 'rgba(255, 255, 255, 0.3)',
                  overflow: 'hidden'
                }}>
                  <div
                    style={{
                      height: '100%',
                      background: 'rgba(255, 255, 255, 0.6)',
                      animation: 'slide 2s infinite',
                      width: '30%'
                    }}
                  />
                </div>
              )}
            </AgentCard>
          );
        })}
      </AgentGrid>
    </ProgressContainer>
  );
};

export default AnalysisProgress;


