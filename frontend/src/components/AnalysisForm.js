import React, { useState } from 'react';
import styled from 'styled-components';
import { Github, Calendar, Settings, Play } from 'lucide-react';

const FormContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2.5rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-width: 600px;
  margin: 2rem auto;
`;

const FormTitle = styled.h2`
  margin: 0 0 1.5rem 0;
  color: #2d3748;
  font-size: 1.875rem;
  font-weight: 700;
  text-align: center;
`;

const FormDescription = styled.p`
  color: #4a5568;
  text-align: center;
  margin-bottom: 2rem;
  line-height: 1.6;
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: white;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  
  &::placeholder {
    color: #a0aec0;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: white;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const SubmitButton = styled.button`
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const HelpText = styled.div`
  font-size: 0.875rem;
  color: #718096;
  margin-top: 0.5rem;
`;

const ExampleRepos = styled.div`
  margin-top: 1rem;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
`;

const ExampleTitle = styled.div`
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
`;

const ExampleList = styled.ul`
  margin: 0;
  padding-left: 1rem;
  color: #4a5568;
  font-size: 0.875rem;
`;

const AnalysisForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    repository_url: '',
    analysis_period_days: 90,
    include_closed_issues: true
  });

  const [isDemoMode, setIsDemoMode] = useState(false);

  // Check if backend is in demo mode
  React.useEffect(() => {
    const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    fetch(`${apiBaseUrl}/health`)
      .then(res => res.json())
      .then(data => setIsDemoMode(data.demo_mode))
      .catch(() => setIsDemoMode(false));
  }, []);

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExampleClick = (repoUrl) => {
    setFormData(prev => ({ ...prev, repository_url: repoUrl }));
  };

  return (
    <FormContainer>
      <FormTitle>Repository Analysis</FormTitle>
      {isDemoMode && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea22 0%, #764ba222 100%)',
          border: '2px solid #667eea',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{ fontWeight: 'bold', color: '#667eea', marginBottom: '0.5rem' }}>
            🎭 Demo Mode Active
          </div>
          <div style={{ fontSize: '0.875rem', color: '#4a5568' }}>
            No API keys required! Using realistic mock data to showcase all features.
          </div>
        </div>
      )}
      <FormDescription>
        Analyze GitHub repository issue trends using our advanced multi-agent system. 
        Get insights on maintenance load, community health, and strategic recommendations.
      </FormDescription>
      
      <form onSubmit={handleSubmit}>
        <FormGroup>
          <Label>
            <Github size={16} />
            Repository URL
          </Label>
          <Input
            type="text"
            name="repository_url"
            value={formData.repository_url}
            onChange={handleChange}
            placeholder="e.g., microsoft/vscode or https://github.com/microsoft/vscode"
            required
          />
          <HelpText>
            Enter the GitHub repository URL or just the owner/repository format
          </HelpText>
        </FormGroup>

        <FormGroup>
          <Label>
            <Calendar size={16} />
            Analysis Period
          </Label>
          <Select
            name="analysis_period_days"
            value={formData.analysis_period_days}
            onChange={handleChange}
          >
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 2 months</option>
            <option value={90}>Last 3 months</option>
            <option value={180}>Last 6 months</option>
            <option value={365}>Last year</option>
          </Select>
          <HelpText>
            How far back to analyze issue trends
          </HelpText>
        </FormGroup>

        <FormGroup>
          <Label>
            <Settings size={16} />
            Analysis Options
          </Label>
          <div style={{ marginTop: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="include_closed_issues"
                checked={formData.include_closed_issues}
                onChange={handleChange}
              />
              <span>Include closed issues in analysis</span>
            </label>
          </div>
          <HelpText>
            Including closed issues provides more comprehensive trend analysis
          </HelpText>
        </FormGroup>

        <SubmitButton type="submit" disabled={isSubmitting}>
          <Play size={20} />
          {isSubmitting ? 'Starting Analysis...' : 'Start Analysis'}
        </SubmitButton>
      </form>

        <ExampleRepos>
        <ExampleTitle>
          {isDemoMode ? 'Demo repositories (realistic mock data):' : 'Popular repositories to try:'}
        </ExampleTitle>
        <ExampleList>
          <li>
            <button
              type="button"
              style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => handleExampleClick(isDemoMode ? 'microsoft/vscode-demo' : 'microsoft/vscode')}
            >
              {isDemoMode ? 'microsoft/vscode-demo' : 'microsoft/vscode'}
            </button> - Popular code editor
          </li>
          <li>
            <button
              type="button"
              style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => handleExampleClick(isDemoMode ? 'facebook/react-demo' : 'facebook/react')}
            >
              {isDemoMode ? 'facebook/react-demo' : 'facebook/react'}
            </button> - React JavaScript library
          </li>
          <li>
            <button
              type="button"
              style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => handleExampleClick(isDemoMode ? 'tensorflow/tensorflow-demo' : 'tensorflow/tensorflow')}
            >
              {isDemoMode ? 'tensorflow/tensorflow-demo' : 'tensorflow/tensorflow'}
            </button> - Machine learning platform
          </li>
        </ExampleList>
        {isDemoMode && (
          <div style={{ 
            marginTop: '1rem', 
            fontSize: '0.875rem', 
            color: '#4a5568',
            fontStyle: 'italic'
          }}>
            💡 Demo mode generates realistic issue data, trends, and insights without requiring actual repository access.
          </div>
        )}
      </ExampleRepos>
    </FormContainer>
  );
};

export default AnalysisForm;
