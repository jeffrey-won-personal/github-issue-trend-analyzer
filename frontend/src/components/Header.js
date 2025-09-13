import React from 'react';
import styled from 'styled-components';
import { Bot, GitBranch, TrendingUp } from 'lucide-react';

const HeaderContainer = styled.header`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
`;

const HeaderContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
`;

const IconContainer = styled.div`
  display: flex;
  gap: 0.5rem;
  opacity: 0.8;
`;

const Title = styled.h1`
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 0.875rem;
  opacity: 0.8;
  color: white;
`;

const Header = () => {
  const [isDemoMode, setIsDemoMode] = React.useState(false);

  React.useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setIsDemoMode(data.demo_mode))
      .catch(() => setIsDemoMode(false));
  }, []);

  return (
    <HeaderContainer>
      <HeaderContent>
        <Logo>
          <IconContainer>
            <Bot size={24} />
            <GitBranch size={20} />
            <TrendingUp size={20} />
          </IconContainer>
          <div>
            <Title>GitHub Issue Trend Analyzer</Title>
            <Subtitle>Multi-Agent Repository Intelligence</Subtitle>
          </div>
        </Logo>
        
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '1rem',
          color: 'white', 
          fontSize: '0.875rem', 
          opacity: 0.8 
        }}>
          {isDemoMode && (
            <div style={{
              background: 'rgba(255, 255, 255, 0.2)',
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: '600'
            }}>
              🎭 DEMO MODE
            </div>
          )}
          <span>Powered by LangGraph</span>
        </div>
      </HeaderContent>
    </HeaderContainer>
  );
};

export default Header;
