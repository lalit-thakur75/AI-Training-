import React, { useState, useEffect } from 'react';
import ChatArea from './components/ChatArea';
import MessageInput from './components/MessageInput';
import DocumentWorkspace from './components/DocumentWorkspace';
import {
  checkHealth,
  sendChatMessage,
  generateImage,
  fetchProviderStatus,
  fetchProviderDiagnostics,
  fetchConversations,
  fetchConversationHistory,
  deleteConversation
} from './services/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [health, setHealth] = useState({
    status: 'checking...',
    database: { connected: false },
    configured_providers: {}
  });
  const [providers, setProviders] = useState([]);
  const [testingProviders, setTestingProviders] = useState(false);
  const [diagMessage, setDiagMessage] = useState('');

  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [attachedDoc, setAttachedDoc] = useState(null);

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "👋 Hello! I am your Multimodal AI Personal Assistant.\n\nHere is what you can do:\n• 💬 Chat with me on any topic.\n• 📷 Attach an image for visual question answering or paragraph summary.\n• 📄 Attach a document (PDF/TXT/DOCX) directly to ask questions from it.\n• 🎙️ Click the mic and speak — speech will transcribe in real-time.\n• 🎨 Generate images freely using the palette button.\n• 🌐 Toggle Web Search for live, cited facts.\n• 💖 Toggle Emotional Care for compassionate support.",
      created_at: new Date().toLocaleTimeString()
    }
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState('standard'); // 'standard', 'emotional', or 'rag'
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [showWorkspace, setShowWorkspace] = useState(false);

  const loadConversations = async () => {
    try {
      const data = await fetchConversations();
      setConversations(data || []);
    } catch (e) {
      console.warn('Could not load past conversations:', e);
    }
  };

  // Initial load
  useEffect(() => {
    checkHealth().then((data) => setHealth(data));
    fetchProviderStatus().then((d) => setProviders(d.providers || []));
    loadConversations();
  }, []);

  const handleTestProviders = async () => {
    setTestingProviders(true);
    setDiagMessage('');
    try {
      const results = await fetchProviderDiagnostics();
      const summary = results.map(r => `${r.name}: ${r.verified ? 'Verified ✓' : (r.configured ? 'Error: ' + (r.error || 'Failed') : 'Missing Key')}`).join(' | ');
      setDiagMessage(summary);
    } catch (e) {
      setDiagMessage(`Test failed: ${e.message}`);
    } finally {
      setTestingProviders(false);
    }
  };

  const handleSelectConversation = async (convId) => {
    if (convId === conversationId) return;
    setIsLoading(true);
    try {
      const data = await fetchConversationHistory(convId);
      setConversationId(data.id);
      if (data.messages && data.messages.length > 0) {
        setMessages(data.messages);
      } else {
        setMessages([
          {
            id: 'resume',
            role: 'assistant',
            content: `Resumed conversation: "${data.title}"`,
            created_at: new Date().toLocaleTimeString()
          }
        ]);
      }
    } catch (err) {
      alert(`Could not load chat history: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this chat history?')) return;
    try {
      await deleteConversation(convId);
      if (conversationId === convId) {
        startNewChat();
      }
      loadConversations();
    } catch (err) {
      alert(`Failed to delete chat: ${err.message}`);
    }
  };

  const handleSendMessage = async (text, docIdOverride) => {
    const userMsg = {
      id: String(Date.now()),
      role: 'user',
      content: text,
      created_at: new Date().toLocaleTimeString()
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const activeDocId = docIdOverride || attachedDoc?.id || null;
      const response = await sendChatMessage({
        message: text,
        conversation_id: conversationId,
        mode: activeDocId ? 'rag' : mode,
        search_enabled: webSearchEnabled,
        voice_response: false,
        document_id: activeDocId
      });

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const asstMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response.reply,
        sources: response.sources,
        audio_base64: response.audio_base64,
        crisis_flag: response.crisis_flag,
        created_at: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, asstMsg]);
      loadConversations();
    } catch (err) {
      const errorMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: `⚠️ Error: ${err.message}. Please verify the backend server is running.`,
        created_at: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendImage = async (imageFile, userPrompt) => {
    const previewUrl = URL.createObjectURL(imageFile);
    const userMsg = {
      id: String(Date.now()),
      role: 'user',
      content: userPrompt || 'What is in this image?',
      image_url: previewUrl,
      created_at: new Date().toLocaleTimeString()
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('prompt', userPrompt || '');
      if (conversationId) formData.append('conversation_id', conversationId);

      const res = await fetch(`${API_BASE_URL}/chat/image`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Image processing failed');
      }

      const response = await res.json();
      if (response.conversation_id) setConversationId(response.conversation_id);

      const asstMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response.reply,
        sources: response.sources || [],
        created_at: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, asstMsg]);
      loadConversations();
    } catch (err) {
      const errorMsg = {
        id: String(Date.now() + 2),
        role: 'assistant',
        content: `⚠️ Image analysis error: ${err.message}.`,
        created_at: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateImage = async (prompt) => {
    const userMsg = {
      id: String(Date.now()),
      role: 'user',
      content: `🎨 Generate image: ${prompt}`,
      created_at: new Date().toLocaleTimeString()
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await generateImage(prompt, conversationId);
      if (response.conversation_id) setConversationId(response.conversation_id);

      const asstMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response.reply,
        image_url: response.image_url,
        provider_used: response.provider_used,
        created_at: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, asstMsg]);
      loadConversations();
    } catch (err) {
      const errorMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: `⚠️ Image generation failed: ${err.message}`,
        created_at: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setConversationId(null);
    setAttachedDoc(null);
    setMessages([
      {
        id: 'new-chat',
        role: 'assistant',
        content: 'Started a fresh conversation. How can I help you today?',
        created_at: new Date().toLocaleTimeString()
      }
    ]);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">🤖</span>
          <div>
            <div className="sidebar-title">Multimodal AI</div>
            <div className="sidebar-subtitle">Personal Assistant MVP</div>
          </div>
        </div>

        <button className="btn-new-chat" onClick={startNewChat}>
          + New Conversation
        </button>

        {/* Saved Chat History List */}
        <div className="conversations-history" style={{
          marginTop: '0.8rem',
          maxHeight: '190px',
          overflowY: 'auto',
          borderBottom: '1px solid #1e293b',
          paddingBottom: '0.6rem'
        }}>
          <div style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            color: '#94a3b8',
            marginBottom: '0.4rem',
            textTransform: 'uppercase',
            letterSpacing: '0.04em'
          }}>
            Saved Chats ({conversations.length})
          </div>
          {conversations.length === 0 ? (
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic', padding: '3px 0' }}>
              No chats saved yet
            </div>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => handleSelectConversation(c.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '5px 8px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  marginBottom: '2px',
                  background: conversationId === c.id ? '#1e293b' : 'transparent',
                  color: conversationId === c.id ? '#60a5fa' : '#cbd5e1',
                  transition: 'background 0.15s'
                }}
              >
                <span style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  maxWidth: '140px'
                }} title={c.title}>
                  💬 {c.title}
                </span>
                <button
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#64748b',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    padding: '2px'
                  }}
                  title="Delete chat"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        <div className="sidebar-nav">
          <div className="nav-item active">💬 Active Chat</div>
          <div
            className={`nav-item ${showWorkspace ? 'active' : ''}`}
            onClick={() => setShowWorkspace(!showWorkspace)}
          >
            📄 Document Workspace
          </div>

          {/* AI Providers Section */}
          <div style={{ marginTop: '0.8rem', borderTop: '1px solid #1e293b', paddingTop: '0.6rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>AI PROVIDERS (4)</span>
              <button
                onClick={handleTestProviders}
                disabled={testingProviders}
                style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: '0.7rem', padding: 0 }}
                title="Test API connectivity safely"
              >
                {testingProviders ? 'Testing...' : 'Test All'}
              </button>
            </div>
            {providers.map((p) => (
              <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', padding: '3px 0', color: '#cbd5e1' }}>
                <span title={`Model: ${p.model}`}>
                  {p.name === 'xai' ? 'Grok (xAI)' : p.name === 'huggingface' ? 'Hugging Face' : p.name.charAt(0).toUpperCase() + p.name.slice(1)}
                  {p.supports_vision ? ' 👁️' : ''}
                </span>
                <span style={{ color: p.configured ? '#4ade80' : '#64748b', fontSize: '0.7rem' }}>
                  {p.configured ? '● Ready' : '○ Missing'}
                </span>
              </div>
            ))}
            {diagMessage && (
              <div style={{ fontSize: '0.65rem', color: '#93c5fd', marginTop: '0.4rem', background: '#1e293b', padding: '4px', borderRadius: '4px', wordBreak: 'break-word' }}>
                {diagMessage}
              </div>
            )}
          </div>
        </div>

        <div className="sidebar-footer">
          <div>Backend Status:</div>
          <span className={`status-badge ${health.status === 'healthy' ? 'online' : 'offline'}`}>
            ● {health.status === 'healthy' ? 'FastAPI Online' : 'FastAPI Connecting / Degraded'}
          </span>
          <div style={{ marginTop: '0.4rem', fontSize: '0.7rem' }}>
            DB: {health.database?.type || 'sqlite'} (Chats Auto-Saved ✓)
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <main className="main-content">
        {/* Header with Mode Toggles */}
        <header className="app-header">
          <div className="header-left">
            <span className="header-title">
              {mode === 'emotional' ? '💖 Emotional Support Mode' : '💬 Assistant Chat'}
            </span>
          </div>

          <div className="header-controls">
            <button
              className={`toggle-btn ${webSearchEnabled ? 'active' : ''}`}
              onClick={() => setWebSearchEnabled(!webSearchEnabled)}
              title="Search the live web for fresh information"
            >
              🌐 Web Search {webSearchEnabled ? 'ON' : 'OFF'}
            </button>

            <button
              className={`toggle-btn ${mode === 'emotional' ? 'active emotional' : ''}`}
              onClick={() => setMode(mode === 'emotional' ? 'standard' : 'emotional')}
              title="Switch to empathetic, supportive conversation mode"
            >
              💖 Emotional Care {mode === 'emotional' ? 'ON' : 'OFF'}
            </button>

            <button
              className={`toggle-btn ${showWorkspace ? 'active' : ''}`}
              onClick={() => setShowWorkspace(!showWorkspace)}
              title="Toggle Document Workspace"
            >
              📄 Workspace {showWorkspace ? 'Open' : 'Closed'}
            </button>
          </div>
        </header>

        {/* Workspace Container */}
        <div className="workspace-container">
          <div className="chat-panel">
            <ChatArea
              messages={messages}
              isLoading={isLoading}
              mode={mode}
            />
            <MessageInput
              onSendMessage={handleSendMessage}
              onSendImage={handleSendImage}
              onGenerateImage={handleGenerateImage}
              disabled={isLoading}
              placeholder={
                mode === 'emotional'
                  ? "I'm here to listen. How are you feeling today?"
                  : attachedDoc
                  ? `Ask question from ${attachedDoc.filename}...`
                  : "Type a question, attach an image/doc, or speak via mic..."
              }
              attachedDoc={attachedDoc}
              onAttachDoc={(doc) => {
                setAttachedDoc(doc);
                setMessages((prev) => [
                  ...prev,
                  {
                    id: String(Date.now()),
                    role: 'assistant',
                    content: `📄 **${doc.filename}** attached and indexed! You can now ask questions about this document directly.`,
                    created_at: new Date().toLocaleTimeString()
                  }
                ]);
              }}
              onDetachDoc={() => setAttachedDoc(null)}
            />
          </div>

          {showWorkspace && (
            <DocumentWorkspace
              onClose={() => setShowWorkspace(false)}
              onDocumentUpdated={() => {
                setMessages((prev) => [
                  ...prev,
                  {
                    id: String(Date.now()),
                    role: 'assistant',
                    content: 'ℹ️ Document updated and re-indexed. You can now ask questions about the updated document in chat!',
                    created_at: new Date().toLocaleTimeString()
                  }
                ]);
              }}
            />
          )}
        </div>
      </main>
    </div>
  );
}
