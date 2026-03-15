import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App Layout Integration', () => {
  it('renders Sidebar and unified Chat view without crashing', () => {
    render(<App />);

    // Check Sidebar is there
    expect(screen.getByText(/Market Analyst/i)).toBeInTheDocument();

    // Check unified ChatPanel is rendered (single query box)
    expect(screen.getByText(/Ask anything about the market/i)).toBeInTheDocument();

    // Check usage hints are visible in sidebar
    expect(screen.getByText(/How to use/i)).toBeInTheDocument();
  });

  it('does not render multi-mode navigation buttons', () => {
    render(<App />);

    // Old multi-mode nav items should not exist
    expect(screen.queryByText('Analyze')).not.toBeInTheDocument();
    expect(screen.queryByText('Compare')).not.toBeInTheDocument();
    expect(screen.queryByText('Portfolio')).not.toBeInTheDocument();
  });
});
