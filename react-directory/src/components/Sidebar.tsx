import React from 'react';
import { LayoutDashboard, MessageSquare, Briefcase, BarChart2 } from 'lucide-react';
import { motion } from 'framer-motion';

export type ViewType = 'dashboard' | 'chat' | 'portfolio' | 'compare';

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
}

const navItems = [
  { id: 'dashboard', label: 'Analyze', icon: LayoutDashboard },
  { id: 'compare', label: 'Compare', icon: BarChart2 },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase },
  { id: 'chat', label: 'AI Chat', icon: MessageSquare },
] as const;

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onViewChange }) => {
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

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          const Icon = item.icon;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => onViewChange(item.id as ViewType)}
              whileHover={{ scale: 1.02, backgroundColor: 'var(--bg-surface-hover)' }}
              whileTap={{ scale: 0.98 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                borderRadius: '12px',
                border: 'none',
                background: isActive ? 'var(--bg-surface)' : 'transparent',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '15px',
                fontWeight: isActive ? 500 : 400,
                transition: 'color 0.2s ease',
              }}
            >
              <Icon size={20} color={isActive ? 'var(--accent-color)' : 'currentColor'} />
              {item.label}
              {isActive && (
                <motion.div
                  layoutId="active-indicator"
                  style={{
                    position: 'absolute',
                    left: 0,
                    width: '3px',
                    height: '24px',
                    background: 'var(--accent-color)',
                    borderRadius: '0 4px 4px 0'
                  }}
                />
              )}
            </motion.button>
          );
        })}
      </nav>
    </div>
  );
};
