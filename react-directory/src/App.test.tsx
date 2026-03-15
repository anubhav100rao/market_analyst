import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App Layout Integration', () => {
  it('renders Sidebar and default Chat view without crashing', () => {
    render(<App />);
    
    // Check Sidebar is there
    expect(screen.getByText(/Market Analyst/i)).toBeInTheDocument();
    
    // Check default view text in ChatPanel is rendered
    expect(screen.getByText(/Ask anything about the market/i)).toBeInTheDocument();
    
    // Switch view
    const analyzeButton = screen.getByText('Analyze');
    fireEvent.click(analyzeButton);
    
    // Ensure the new view rendered correctly
    expect(screen.getByText('Analyze Single Stock')).toBeInTheDocument();
  });
});
