import React, { useState } from 'react';
import { api } from '../api';
import { getErrorMessage } from '../error';
import type { AnalysisResponse } from '../types';
import { Loader2, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { StockCard } from './StockCard';

export const ChatPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState('');

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');
    setResponse(null);

    try {
      const res = await api.chat({ query });
      setResponse(res);
    } catch (error: unknown) {
      console.error('[ChatPanel] chat request failed', error);
      setError(getErrorMessage(error, 'Error communicating with AI'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
      
      {/* Response Area */}
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '12px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {!response && !isLoading && !error && (
          <div style={{ margin: 'auto', textAlign: 'center', opacity: 0.5 }}>
            <p>Ask anything about the market.</p>
            <p style={{ fontSize: '13px' }}>e.g. "Compare Tata Motors and Mahindra"</p>
          </div>
        )}

        {isLoading && (
          <div style={{ margin: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <Loader2 size={32} className="animate-spin" color="var(--accent-color)" />
            <p style={{ color: 'var(--text-secondary)' }}>Analyzing market data...</p>
          </div>
        )}

        {error && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} 
            style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '12px', border: '1px solid var(--danger)' }}>
            {error}
          </motion.div>
        )}

        <AnimatePresence>
          {response && (
            <motion.div 
              initial={{opacity: 0, y: 20}} animate={{opacity: 1, y: 0}}
              style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
            >
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>Verdict: <span style={{ color: 'var(--accent-color)'}}>{response.recommendation}</span></h3>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{response.reasoning}</p>
              </div>

              {response.stocks.map(stock => (
                <StockCard key={stock.stock} data={stock} />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask Market Analyst AI..."
          className="glass-panel"
          style={{
            width: '100%',
            padding: '16px 50px 16px 20px',
            fontSize: '16px',
            border: '1px solid var(--border-color)',
            borderRadius: '16px',
            color: 'var(--text-primary)',
            background: 'var(--bg-surface)',
            outline: 'none',
          }}
          disabled={isLoading}
        />
        <button 
          type="submit" 
          disabled={!query.trim() || isLoading}
          style={{
            position: 'absolute',
            right: '8px',
            top: '8px',
            bottom: '8px',
            width: '40px',
            background: query.trim() && !isLoading ? 'var(--accent-color)' : 'transparent',
            border: 'none',
            borderRadius: '12px',
            color: query.trim() && !isLoading ? '#fff' : 'var(--text-secondary)',
            cursor: query.trim() && !isLoading ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </form>
    </div>
  );
};
