import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';

function App() {
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'var(--bg-color)' }}>
      <Sidebar />

      <main style={{ flex: 1, padding: '32px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px',
          margin: '0 auto',
          height: '100%',
          position: 'relative'
        }}>
          <ChatPanel />
        </div>
      </main>
    </div>
  );
}

export default App;
