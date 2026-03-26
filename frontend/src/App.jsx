import React, { useState, useEffect, useRef } from 'react';
import { Search, Send, Loader2, User, Bot, Globe, FileText, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    { role: 'bot', type: 'text', content: "Hello! I'm your OpenClaw Research Agent. Who would you like me to research today?" }
  ]);
  const [loading, setLoading] = useState(false);
  const [currentStatus, setCurrentStatus] = useState('');
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStatus]);

  const handleResearch = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const target = query.trim();
    setQuery('');
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', type: 'text', content: target }]);

    // API base URL can be configured for split frontend/backend deployments.
    const configuredBase = import.meta.env.VITE_API_BASE_URL?.trim();
    const isLocalDev = window.location.origin.includes('localhost:5173') || window.location.origin.includes('localhost:3000');
    const baseUrl = configuredBase || (isLocalDev ? 'http://localhost:8000' : '');
    const eventSource = new EventSource(`${baseUrl}/research?target=${encodeURIComponent(target)}`);

    eventSource.addEventListener('update', (event) => {
      const data = JSON.parse(event.data);
      setCurrentStatus(data.message);
    });

    eventSource.addEventListener('result', (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, { role: 'bot', type: 'report', content: data.content }]);
      setLoading(false);
      setCurrentStatus('');
      eventSource.close();
    });

    eventSource.addEventListener('error', () => {
      setMessages(prev => [...prev, { role: 'bot', type: 'text', content: '⚠️ Connection error. Please try again in a few seconds.' }]);
      setLoading(false);
      setCurrentStatus('');
      eventSource.close();
    });
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>OpenClaw Agent</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Autonomous Internet Exploration</p>
      </header>

      <div className="chat-box glass-panel">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '0.8rem', opacity: 0.7 }}>
              {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              <span>{msg.role === 'user' ? 'You' : 'OpenClaw Agent'}</span>
            </div>
            {msg.type === 'report' ? (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              </div>
            ) : (
              <p style={{ margin: 0 }}>{msg.content}</p>
            )}
          </div>
        ))}
        {loading && (
          <div className="message bot" style={{ background: 'transparent' }}>
            <div className="status-indicator">
              <Sparkles size={16} color="#c084fc" />
              <span>{currentStatus || 'Initializing agent...'}</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form className="input-area" onSubmit={handleResearch}>
        <input
          type="text"
          placeholder="Enter a founder or CEO name (e.g. Jensen Huang)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="send-btn" disabled={loading}>
          {loading ? <Loader2 className="animate-spin" size={20} color="white" /> : <Send size={20} color="white" />}
        </button>
      </form>
    </div>
  );
}

export default App;
