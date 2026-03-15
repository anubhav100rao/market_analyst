import React, { useState } from 'react';
import { api } from '../api';
import { getErrorMessage } from '../error';
import type { AnalysisResponse, IntentResponse } from '../types';
import { Loader2, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { StockCard } from './StockCard';

const ANALYSIS_TYPE_LABELS: Record<string, string> = {
  single: 'Single Stock Analysis',
  compare: 'Stock Comparison',
  portfolio: 'Portfolio Analysis',
};

const IntentBadges: React.FC<{ intent: IntentResponse }> = ({ intent }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
    <span style={{
      padding: '4px 12px',
      borderRadius: '16px',
      fontSize: '13px',
      fontWeight: 600,
      background: 'rgba(99, 102, 241, 0.15)',
      color: 'var(--accent-color)',
      border: '1px solid rgba(99, 102, 241, 0.3)',
    }}>
      {ANALYSIS_TYPE_LABELS[intent.analysis_type] || intent.analysis_type}
    </span>
    {intent.stocks.map(ticker => (
      <span key={ticker} style={{
        padding: '4px 12px',
        borderRadius: '16px',
        fontSize: '13px',
        fontWeight: 600,
        background: 'rgba(16, 185, 129, 0.15)',
        color: 'var(--success)',
        border: '1px solid rgba(16, 185, 129, 0.3)',
      }}>
        {ticker}
      </span>
    ))}
    {intent.parsed_query && (
      <span style={{ fontSize: '12px', color: 'var(--text-secondary)', alignSelf: 'center' }}>
        Parsed: {intent.parsed_query}
      </span>
    )}
  </div>
);

export const ChatPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [response, setResponse] = useState<AnalysisResponse | null>(null);
  const [intent, setIntent] = useState<IntentResponse | null>(null);
  const [error, setError] = useState('');

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');
    setResponse(null);
    setIntent(null);

    try {
      // Step 1: Parse intent to show detected stocks/type
      setLoadingStage('Understanding your query...');
      const intentResult = await api.parseIntent({ query });
      setIntent(intentResult);

      if (!intentResult.stocks || intentResult.stocks.length === 0) {
        setError('Could not identify any stocks in your query. Try mentioning specific stock names like Reliance, TCS, Infosys, etc.');
        setIsLoading(false);
        return;
      }

      // Step 2: Run full analysis
      setLoadingStage('Running analysis...');
      const res = await api.chat({ query });
      setResponse(res);
    } catch (error: unknown) {
      console.error('[ChatPanel] request failed', error);
      setError(getErrorMessage(error, 'Error communicating with AI'));
    } finally {
      setIsLoading(false);
      setLoadingStage('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>

      {/* Response Area */}
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '12px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {!response && !isLoading && !error && !intent && (
          <div style={{ margin: 'auto', textAlign: 'center', opacity: 0.5 }}>
            <p>Ask anything about the market.</p>
            <p style={{ fontSize: '13px', marginTop: '8px' }}>
              e.g. "How is Reliance doing?" &middot; "Compare TCS and Infosys" &middot; "Analyze Reliance, TCS, HDFC Bank"
            </p>
          </div>
        )}

        {isLoading && (
          <div style={{ margin: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            {intent && <IntentBadges intent={intent} />}
            <Loader2 size={32} className="animate-spin" color="var(--accent-color)" />
            <p style={{ color: 'var(--text-secondary)' }}>{loadingStage}</p>
          </div>
        )}

        {error && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}}>
            {intent && <IntentBadges intent={intent} />}
            <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '12px', border: '1px solid var(--danger)' }}>
              {error}
            </div>
          </motion.div>
        )}

        <AnimatePresence>
          {response && (
            <motion.div
              initial={{opacity: 0, y: 20}} animate={{opacity: 1, y: 0}}
              style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
            >
              {intent && <IntentBadges intent={intent} />}

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
          placeholder="e.g. How is Reliance doing? / Compare TCS and Infosys"
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
