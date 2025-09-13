import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import AnalysisForm from './components/AnalysisForm';
import AnalysisProgress from './components/AnalysisProgress';
import ResultsDashboard from './components/ResultsDashboard';
import AgentVisualization from './components/AgentVisualization';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
`;

const MainContent = styled.main`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: calc(100vh - 80px);
`;

const App = () => {
  const [analysisState, setAnalysisState] = useState('idle'); // idle, running, completed, error
  const [sessionData, setSessionData] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [websocket, setWebsocket] = useState(null);

  useEffect(() => {
    // Cleanup websocket on unmount
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [websocket]);

  const startAnalysis = async (analysisRequest) => {
    try {
      setAnalysisState('running');
      
      const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisRequest),
      });

      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }

      const data = await response.json();
      setCurrentSession(data.session_id);
      
      // Initialize session data for UI
      const initialSessionData = {
        session_id: data.session_id,
        current_step: 'initializing',
        completion_percentage: 0,
        agent_statuses: {},
        latest_progress: null
      };
      console.log('Setting initial session data:', initialSessionData);
      setSessionData(initialSessionData);
      
      // Connect to WebSocket for real-time updates
      connectWebSocket(data.session_id);
      
      // Start polling immediately as fallback (WebSocket might not work in Docker)
      console.log('Starting fallback polling...');
      startPolling(data.session_id);
      
    } catch (error) {
      console.error('Error starting analysis:', error);
      setAnalysisState('error');
    }
  };

  const connectWebSocket = (sessionId) => {
    // Use environment variable for WebSocket URL, fallback to current host
    // For development, try localhost first, then fallback to environment variable
    const wsBaseUrl = process.env.REACT_APP_WS_URL || `ws://localhost:8000`;
    const wsUrl = `${wsBaseUrl}/ws/${sessionId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        console.log('Message type:', data.type);
        console.log('Current analysis state:', analysisState);
        
        if (data.type === 'state_update') {
          console.log('Processing state update:', data);
          console.log('Completion percentage:', data.completion_percentage);
          console.log('Current step:', data.current_step);
          setSessionData(data);
          
          if (data.completion_percentage >= 100) {
            console.log('Analysis completed, loading results...');
            setAnalysisState('completed');
            loadResults(sessionId);
          }
        } else if (data.type === 'error') {
          console.error('Analysis error:', data.error);
          setAnalysisState('error');
        } else if (data.type === 'connection_established') {
          console.log('WebSocket connection established');
        } else {
          console.log('Unknown message type:', data.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
        console.error('Raw message:', event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setAnalysisState('error');
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      if (event.code !== 1000) {
        console.error('WebSocket closed unexpectedly');
        setAnalysisState('error');
      }
    };

    setWebsocket(ws);
  };

  const startPolling = (sessionId) => {
    const pollInterval = setInterval(async () => {
      try {
        const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBaseUrl}/status/${sessionId}`);
        const data = await response.json();
        
        console.log('Polling status:', data);
        console.log('Polling - Completion percentage:', data.completion_percentage);
        console.log('Polling - Current step:', data.current_step);
        setSessionData({
          session_id: sessionId,
          current_step: data.current_step,
          completion_percentage: data.completion_percentage,
          agent_statuses: data.agent_statuses,
          latest_progress: data.latest_update
        });
        
        if (data.completion_percentage >= 100) {
          clearInterval(pollInterval);
          setAnalysisState('completed');
          loadResults(sessionId);
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
        setAnalysisState('error');
      }
    }, 2000);
    
    // Store interval ID for cleanup
    setWebsocket({ close: () => clearInterval(pollInterval) });
  };

  const loadResults = async (sessionId) => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/results/${sessionId}`);
      const results = await response.json();
      setSessionData(prev => ({ ...prev, results }));
    } catch (error) {
      console.error('Error loading results:', error);
    }
  };

  const resetAnalysis = () => {
    setCurrentSession(null);
    setAnalysisState('idle');
    setSessionData(null);
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
  };

  return (
    <Router future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <AppContainer>
        <Header />
        <MainContent>
          <Routes>
            <Route 
              path="/" 
              element={
                <div>
                  {analysisState === 'idle' && (
                    <AnalysisForm onSubmit={startAnalysis} />
                  )}
                  
                  {analysisState === 'running' && sessionData && (
                    <div>
                      <AnalysisProgress sessionData={sessionData} />
                      <AgentVisualization sessionData={sessionData} />
                    </div>
                  )}
                  
                  {analysisState === 'completed' && (
                    sessionData?.results ? (
                      <ResultsDashboard 
                        results={sessionData.results} 
                        onReset={resetAnalysis}
                      />
                    ) : (
                      <div style={{ 
                        background: 'rgba(255, 255, 255, 0.95)', 
                        padding: '2rem', 
                        borderRadius: '16px',
                        textAlign: 'center',
                        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)'
                      }}>
                        <h2 style={{ color: '#2d3748', marginBottom: '1rem' }}>Analysis Complete</h2>
                        <p style={{ color: '#4a5568', marginBottom: '2rem' }}>Loading results...</p>
                        <div style={{ 
                          display: 'inline-block',
                          width: '40px',
                          height: '40px',
                          border: '4px solid #e2e8f0',
                          borderTop: '4px solid #667eea',
                          borderRadius: '50%',
                          animation: 'spin 1s linear infinite'
                        }} />
                      </div>
                    )
                  )}
                  
                  {analysisState === 'error' && (
                    <div style={{ 
                      background: '#fee', 
                      padding: '2rem', 
                      borderRadius: '8px',
                      border: '1px solid #fcc'
                    }}>
                      <h3>Analysis Failed</h3>
                      <p>An error occurred during analysis. Please try again.</p>
                      <button onClick={resetAnalysis}>Start New Analysis</button>
                    </div>
                  )}
                </div>
              } 
            />
          </Routes>
        </MainContent>
      </AppContainer>
    </Router>
  );
};

export default App;

