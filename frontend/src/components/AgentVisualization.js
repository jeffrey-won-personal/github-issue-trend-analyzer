import React, { useState } from 'react';
import styled from 'styled-components';
import { Bot, ArrowRight, Database, BarChart3, Lightbulb, FileText, Activity } from 'lucide-react';

const VisualizationContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  margin: 2rem 0;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const VisualizationHeader = styled.div`
  text-align: center;
  margin-bottom: 2rem;
`;

const Title = styled.h2`
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0;
  color: #4a5568;
  font-size: 1rem;
`;

const WorkflowDiagram = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin: 2rem 0;
  flex-wrap: wrap;
`;

const AgentNode = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  min-width: 120px;
`;

const AgentCircle = styled.div.withConfig({
  shouldForwardProp: (prop) => !['isActive', 'isCompleted', 'isFailed'].includes(prop),
})`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  
  background: ${props => {
    if (props.isActive) return 'linear-gradient(135deg, #4299e1 0%, #3182ce 100%)';
    if (props.isCompleted) return 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
    if (props.isFailed) return 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
    return 'linear-gradient(135deg, #a0aec0 0%, #718096 100%)';
  }};
  
  ${props => props.isActive && `
    animation: pulse 2s infinite;
    box-shadow: 0 0 0 0 rgba(66, 153, 225, 0.7);
  `}
  
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(66, 153, 225, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(66, 153, 225, 0); }
    100% { box-shadow: 0 0 0 0 rgba(66, 153, 225, 0); }
  }
  
  &:hover {
    transform: scale(1.05);
  }
`;

const AgentLabel = styled.div`
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #2d3748;
  max-width: 100px;
`;

const Arrow = styled.div`
  display: flex;
  align-items: center;
  color: #a0aec0;
  margin: 0 0.5rem;
  
  @media (max-width: 768px) {
    transform: rotate(90deg);
    margin: 0.5rem 0;
  }
`;

const AgentDetailsPanel = styled.div`
  background: #f7fafc;
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 2rem;
  border-left: 4px solid #667eea;
`;

const DetailTitle = styled.h3`
  margin: 0 0 1rem 0;
  color: #2d3748;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const DetailContent = styled.div`
  color: #4a5568;
  line-height: 1.6;
`;

const CapabilityList = styled.ul`
  margin: 1rem 0;
  padding-left: 1.5rem;
  
  li {
    margin-bottom: 0.5rem;
    color: #4a5568;
  }
`;

const StatusBadge = styled.span.withConfig({
  shouldForwardProp: (prop) => prop !== 'status',
})`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  
  background: ${props => {
    switch (props.status) {
      case 'completed': return '#c6f6d5';
      case 'running': return '#bee3f8';
      case 'failed': return '#fed7d7';
      default: return '#edf2f7';
    }
  }};
  
  color: ${props => {
    switch (props.status) {
      case 'completed': return '#22543d';
      case 'running': return '#2a4365';
      case 'failed': return '#742a2a';
      default: return '#2d3748';
    }
  }};
`;

const AgentVisualization = ({ sessionData }) => {
  const [selectedAgent, setSelectedAgent] = useState(null);
  
  const { agent_statuses = {}, current_step = '' } = sessionData || {};

  const agents = [
    {
      id: 'data_retrieval_agent',
      name: 'Data Retrieval',
      icon: <Database size={24} />,
      description: 'Intelligent GitHub API integration with rate limiting and data quality assessment',
      capabilities: [
        'GitHub API authentication and rate limiting',
        'Repository metadata extraction',
        'Issue data retrieval with filtering',
        'Data quality assessment using LLM',
        'Error handling and retry mechanisms'
      ]
    },
    {
      id: 'analysis_agent',
      name: 'Time-Series Analysis',
      icon: <BarChart3 size={24} />,
      description: 'Advanced statistical analysis of issue trends with forecasting and anomaly detection',
      capabilities: [
        'Statistical trend analysis',
        'Seasonal pattern detection',
        'Anomaly identification using ML',
        'Time-series forecasting (ARIMA)',
        'Label-based trend segmentation'
      ]
    },
    {
      id: 'insight_agent',
      name: 'Insight Generation',
      icon: <Lightbulb size={24} />,
      description: 'AI-powered strategic insights and recommendations using advanced reasoning',
      capabilities: [
        'Repository health assessment',
        'Maintenance pattern analysis',
        'Community engagement evaluation',
        'Strategic recommendation generation',
        'Risk assessment and mitigation'
      ]
    },
    {
      id: 'report_agent',
      name: 'Report Generation',
      icon: <FileText size={24} />,
      description: 'Comprehensive report synthesis for multiple audiences and use cases',
      capabilities: [
        'Executive summary generation',
        'Technical analysis reports',
        'Actionable recommendations',
        'Dashboard data preparation',
        'Multi-format output support'
      ]
    }
  ];

  const getAgentStatus = (agentId) => {
    return agent_statuses[agentId] || 'pending';
  };

  const isCurrentAgent = (agentId) => {
    return current_step.toLowerCase().includes(agentId.split('_')[0]);
  };

  return (
    <VisualizationContainer>
      <VisualizationHeader>
        <Title>Multi-Agent Workflow Visualization</Title>
        <Subtitle>
          Watch our specialized agents collaborate to analyze your repository
        </Subtitle>
      </VisualizationHeader>

      <WorkflowDiagram>
        {agents.map((agent, index) => {
          const status = getAgentStatus(agent.id);
          const isActive = isCurrentAgent(agent.id) && status === 'running';
          const isCompleted = status === 'completed';
          const isFailed = status === 'failed';

          return (
            <React.Fragment key={agent.id}>
              <AgentNode>
                <AgentCircle
                  isActive={isActive}
                  isCompleted={isCompleted}
                  isFailed={isFailed}
                  onClick={() => setSelectedAgent(agent)}
                >
                  {agent.icon}
                  {isActive && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '-5px',
                        right: '-5px',
                        width: '20px',
                        height: '20px',
                        background: '#4299e1',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <Activity size={12} />
                    </div>
                  )}
                </AgentCircle>
                <AgentLabel>{agent.name}</AgentLabel>
                <StatusBadge status={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </StatusBadge>
              </AgentNode>
              
              {index < agents.length - 1 && (
                <Arrow>
                  <ArrowRight size={20} />
                </Arrow>
              )}
            </React.Fragment>
          );
        })}
      </WorkflowDiagram>

      {selectedAgent && (
        <AgentDetailsPanel>
          <DetailTitle>
            {selectedAgent.icon}
            {selectedAgent.name} Agent
            <StatusBadge status={getAgentStatus(selectedAgent.id)}>
              {getAgentStatus(selectedAgent.id).charAt(0).toUpperCase() + 
               getAgentStatus(selectedAgent.id).slice(1)}
            </StatusBadge>
          </DetailTitle>
          
          <DetailContent>
            <p>{selectedAgent.description}</p>
            
            <h4 style={{ margin: '1rem 0 0.5rem 0', color: '#2d3748' }}>Core Capabilities:</h4>
            <CapabilityList>
              {selectedAgent.capabilities.map((capability, index) => (
                <li key={index}>{capability}</li>
              ))}
            </CapabilityList>
          </DetailContent>
        </AgentDetailsPanel>
      )}

      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        background: '#e6fffa',
        borderRadius: '8px',
        border: '1px solid #81e6d9'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Bot size={16} color="#2c7a7b" />
          <strong style={{ color: '#2c7a7b' }}>Multi-Agent Intelligence</strong>
        </div>
        <div style={{ color: '#2c7a7b', fontSize: '0.875rem' }}>
          Each agent specializes in different aspects of repository analysis, collaborating through 
          LangGraph orchestration with intelligent routing, state management, and error recovery.
        </div>
      </div>
    </VisualizationContainer>
  );
};

export default AgentVisualization;


