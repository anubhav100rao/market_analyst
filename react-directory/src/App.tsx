import { useState } from 'react';
import { Sidebar, type ViewType } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { Dashboard } from './components/Dashboard';

function App() {
  const [activeView, setActiveView] = useState<ViewType>('chat');

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'var(--bg-color)' }}>
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      
      <main style={{ flex: 1, padding: '32px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px',
          margin: '0 auto',
          height: '100%',
          position: 'relative'
        }}>
          {activeView === 'chat' && <ChatPanel />}
          {activeView === 'dashboard' && <Dashboard type="analyze" />}
          {activeView === 'compare' && <Dashboard type="compare" />}
          {activeView === 'portfolio' && <Dashboard type="portfolio" />}
        </div>
      </main>
    </div>
  );
}

export default App;
