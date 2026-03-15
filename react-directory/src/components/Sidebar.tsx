import React from 'react';
import { MessageSquare } from 'lucide-react';

export const Sidebar: React.FC = () => {
  return (
    <div style={{
      width: '260px',
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      gap: '32px',
      borderRight: '1px solid var(--border-color)',
      background: 'rgba(13, 14, 21, 0.5)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, var(--accent-color), var(--accent-hover))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '20px'
        }}>
          AI
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 600 }}>Market Analyst</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Pro Edition</p>
        </div>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        borderRadius: '12px',
        background: 'var(--bg-surface)',
        color: 'var(--text-primary)',
        fontSize: '15px',
        fontWeight: 500,
      }}>
        <MessageSquare size={20} color="var(--accent-color)" />
        AI Chat
      </div>

      <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
        <p style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: '8px' }}>How to use</p>
        <p>Just type your question naturally:</p>
        <ul style={{ paddingLeft: '16px', marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <li>"How is Reliance doing?"</li>
          <li>"Compare TCS and Infosys"</li>
          <li>"Analyze Reliance, TCS, HDFC Bank"</li>
        </ul>
        <p style={{ marginTop: '12px', fontSize: '12px', opacity: 0.7 }}>
          AI automatically detects stocks and analysis type from your query.
        </p>
      </div>

      <div style={{ marginTop: 'auto', fontSize: '12px', color: 'var(--text-secondary)', opacity: 0.5 }}>
        Built with LangGraph + Gemini + FastAPI
      </div>
    </div>
  );
};
