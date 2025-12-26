import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Settings, Cpu, Activity, BrainCircuit } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import { LibraryGrid } from './components/LibraryGrid';
import { Reader } from './components/Reader';

// Types
interface Message {
  role: 'user' | 'assistant';
  content: string;
  type?: 'text' | 'math_tandem';
  details?: {
    agent_1: string;
    agent_2: string;
  };
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [viewMode, setViewMode] = useState<'chat' | 'library' | 'reader'>('chat');
  const [selectedBook, setSelectedBook] = useState<string | null>(null);
  const [systemState, setSystemState] = useState<'idle' | 'math_1' | 'math_2' | 'debating'>('idle');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setSystemState('math_1'); // Simulate start

    try {
      // Simulate stepped progress if math (fake delay for UX animation)
      setTimeout(() => setSystemState('math_2'), 1500);
      setTimeout(() => setSystemState('debating'), 3000);

      const res = await axios.post('http://localhost:8001/api/chat', {
        message: userMsg.content,
        history: messages.map(m => ({ role: m.role, content: m.content }))
      });

      const data = res.data;

      const botMsg: Message = {
        role: 'assistant',
        content: data.response,
        type: data.mode === 'math' ? 'math_tandem' : 'text',
        details: data.details,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error communicating with Axiom Core.", timestamp: new Date() }]);
    } finally {
      setLoading(false);
      setSystemState('idle');
    }
  };

  return (
    <div className="app-container">
      {/* Dynamic Background */}
      <div className="ambient-bg"></div>

      {/* Header */}
      <header className="glass-panel header">
        <div className="logo">
          <BrainCircuit color="var(--color-accent-1)" size={28} />
          <h1>AXIOM <span className="sub">MBAD SYSTEM</span></h1>
        </div>
        <button className="icon-btn" onClick={() => setViewMode('library')} title="Neural Library">📚</button> {/* New Library Button */}
        <button className="icon-btn" onClick={() => setShowSettings(true)}><Settings size={20} /></button>
      </header>

      {/* View Mode Switcher Overlay */}
      {viewMode === 'library' && (
        <LibraryGrid
          onSelectBook={(id) => {
            setSelectedBook(id);
            setViewMode('reader');
          }}
          onClose={() => setViewMode('chat')}
        />
      )}

      {/* Reader Interface */}
      {viewMode === 'reader' && selectedBook && (
        <Reader
          bookId={selectedBook}
          onClose={() => setViewMode('library')}
        />
      )}

      {/* Main Chat Area */}
      {viewMode === 'chat' && (
        <div className="chat-area" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="empty-state">
              <Cpu size={64} style={{ opacity: 0.2 }} />
              <p>System Online. Running High-Efficiency SLMs.</p>
              <p className="sub-text">Compact Mathematical Reasoning Kernel Active.</p>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`message-row ${msg.role}`}
              >
                <div className="avatar">
                  {msg.role === 'user' ? 'U' : <BrainCircuit size={16} />}
                </div>
                <div className="bubble glass-panel">
                  {msg.type === 'math_tandem' && msg.details ? (
                    <div className="tandem-result">
                      <div className="tandem-header">
                        <span className="badge agent-1">Agent Alpha</span>
                        <span className="badge agent-2">Agent Beta</span>
                      </div>
                      <div className="tandem-content">
                        <div className="col">{msg.details.agent_1.substring(0, 150)}...</div>
                        <div className="vr"></div>
                        <div className="col">{msg.details.agent_2.substring(0, 150)}...</div>
                      </div>
                      <div className="synthesis-divider">
                        <Activity size={14} /> SYNTHESIS COMPLETE
                      </div>
                      <div className="final-answer">{msg.content}</div>
                    </div>
                  ) : (
                    <div className="text-content">
                      {msg.content}
                      {msg.role === 'assistant' && (
                        <button
                          onClick={() => {
                            window.speechSynthesis.cancel(); // Stop previous
                            const utterance = new SpeechSynthesisUtterance(msg.content);
                            const voices = window.speechSynthesis.getVoices();
                            // Try to prefer a natural English voice
                            const preferredVoice = voices.find(v => (v.name.includes('Google') && v.name.includes('English')) || v.name.includes('Natural')) || voices.find(v => v.lang.includes('en')) || voices[0];
                            if (preferredVoice) utterance.voice = preferredVoice;
                            window.speechSynthesis.speak(utterance);
                          }}
                          style={{
                            marginTop: '10px',
                            fontSize: '0.75rem',
                            color: 'var(--color-accent-2)',
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                          title="Read Aloud"
                        >
                          🔊 Read
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading Indicator */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="system-status"
            >
              <div className="status-line">
                {systemState === 'math_1' && <><span className="dot a1"></span> Agent Alpha Calculating...</>}
                {systemState === 'math_2' && <><span className="dot a2"></span> Agent Beta Verifying...</>}
                {systemState === 'debating' && <><span className="dot coord"></span> Synthesis Engine Active...</>}
              </div>
              <div className="loader-bar">
                <motion.div
                  className="bar-fill"
                  animate={{ width: ["0%", "100%"] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Settings Modal */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              className="glass-panel modal-content"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={e => e.stopPropagation()}
            >
              <h2>System Configuration</h2>
              <div className="setting-group">
                <label>Model Architecture</label>
                <select disabled>
                  <option>Hybrid SLM (Phi-3 + Gemma-2)</option>
                </select>
              </div>
              <div className="setting-group">
                <label>RAG Knowledge Base</label>
                <div className="status-badge success">Active (100k+ docs)</div>
              </div>
              <div className="setting-group">
                <label>Speech Synthesis</label>
                <div className="toggle-row">
                  <span>Auto-Read Responses</span>
                  <input type="checkbox" />
                </div>
              </div>
              <button className="btn-primary full-width" onClick={() => setShowSettings(false)}>
                Save & Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      {viewMode === 'chat' && (
        <div className="input-area glass-panel">
          <input
            type="text"
            placeholder="Enter complex mathematical query..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          />
          <button className="btn-primary" onClick={sendMessage}>
            <Send size={18} />
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
