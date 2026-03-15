import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, DollarSign, PieChart } from 'lucide-react';
import type { StockAnalysis } from '../types';

interface StockCardProps {
  data: StockAnalysis;
}

export const StockCard: React.FC<StockCardProps> = ({ data }) => {
  const getScoreColor = (score: number) => {
    if (score >= 7) return 'var(--success)';
    if (score >= 4) return 'var(--warning)';
    return 'var(--danger)';
  };

  const getScoreStatus = (score: number) => {
    if (score >= 7) return 'Strong';
    if (score >= 4) return 'Neutral';
    return 'Weak';
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel"
      style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600 }}>{data.stock}</h2>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        
        {/* Fundamental */}
        <div style={{ 
          background: 'rgba(0,0,0,0.2)', 
          borderRadius: '12px', 
          padding: '16px',
          borderLeft: `4px solid ${getScoreColor(data.fundamental.score)}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <DollarSign size={18} color="var(--accent-color)" />
            <h3 style={{ fontSize: '16px', fontWeight: 500 }}>Fundamental Analysis</h3>
            <span style={{ marginLeft: 'auto', fontSize: '12px', color: getScoreColor(data.fundamental.score)}}>
              {getScoreStatus(data.fundamental.score)} ({data.fundamental.score}/10)
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <div>P/E: <strong style={{color: 'var(--text-primary)'}}>{data.fundamental.pe_ratio || 'N/A'}</strong></div>
            <div>Margin: <strong style={{color: 'var(--text-primary)'}}>{data.fundamental.profit_margin}</strong></div>
            <div>Grwth: <strong style={{color: 'var(--text-primary)'}}>{data.fundamental.earnings_growth}</strong></div>
            <div>Debt: <strong style={{color: 'var(--text-primary)'}}>{data.fundamental.debt}</strong></div>
          </div>
          <p style={{ marginTop: '12px', fontSize: '13px', lineHeight: 1.5, color: 'var(--text-primary)'}}>
            {data.fundamental.summary}
          </p>
        </div>

        {/* Technical */}
        <div style={{ 
          background: 'rgba(0,0,0,0.2)', 
          borderRadius: '12px', 
          padding: '16px',
          borderLeft: `4px solid ${getScoreColor(data.technical.score)}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Activity size={18} color="var(--accent-color)" />
            <h3 style={{ fontSize: '16px', fontWeight: 500 }}>Technical Analysis</h3>
            <span style={{ marginLeft: 'auto', fontSize: '12px', color: getScoreColor(data.technical.score)}}>
              {getScoreStatus(data.technical.score)} ({data.technical.score}/10)
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <div>RSI: <strong style={{color: 'var(--text-primary)'}}>{data.technical.rsi !== undefined ? data.technical.rsi : 'N/A'}</strong></div>
            <div>Trend: <strong style={{color: 'var(--text-primary)'}}>{data.technical.trend}</strong></div>
            <div style={{gridColumn: 'span 2'}}>MACD: <strong style={{color: 'var(--text-primary)'}}>{data.technical.macd}</strong></div>
          </div>
          <p style={{ marginTop: '12px', fontSize: '13px', lineHeight: 1.5, color: 'var(--text-primary)'}}>
            {data.technical.summary}
          </p>
        </div>

        {/* Sentiment */}
        <div style={{ 
          background: 'rgba(0,0,0,0.2)', 
          borderRadius: '12px', 
          padding: '16px',
          borderLeft: `4px solid ${getScoreColor(data.sentiment.score)}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <PieChart size={18} color="var(--accent-color)" />
            <h3 style={{ fontSize: '16px', fontWeight: 500 }}>Market Sentiment</h3>
            <span style={{ marginLeft: 'auto', fontSize: '12px', color: getScoreColor(data.sentiment.score)}}>
              {getScoreStatus(data.sentiment.score)} ({data.sentiment.score}/10)
            </span>
          </div>
          <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px'}}>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
              <TrendingUp size={14} color="var(--success)" style={{flexShrink: 0, marginTop: '2px'}}/>
              <span color="var(--text-secondary)">
                {data.sentiment.positive_signals.slice(0, 1).join(', ') || 'No major positive news'}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
              <TrendingDown size={14} color="var(--danger)" style={{flexShrink: 0, marginTop: '2px'}}/>
              <span color="var(--text-secondary)">
                {data.sentiment.negative_signals.slice(0, 1).join(', ') || 'No major negative news'}
              </span>
            </div>
          </div>
          <p style={{ marginTop: '12px', fontSize: '13px', lineHeight: 1.5, color: 'var(--text-primary)'}}>
            {data.sentiment.summary}
          </p>
        </div>
        
      </div>
    </motion.div>
  );
};
