import React, { useEffect, useRef } from 'react';
import AudioPlayer from './AudioPlayer';
import SourcesView from './SourcesView';
import CrisisAlert from './CrisisAlert';

export default function ChatArea({ messages, isLoading, mode }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="messages-container">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`message-bubble ${
            msg.role === 'user' ? 'message-user' : 'message-assistant'
          } ${mode === 'emotional' && msg.role === 'assistant' ? 'emotional' : ''}`}
        >
          {/* Header */}
          <div className="message-header">
            <span>
              {msg.role === 'user' ? '👤 You' : '🤖 Assistant'}
              {msg.provider_used && msg.provider_used !== 'none' && msg.provider_used !== 'failed' && (
                <span style={{ marginLeft: '0.4rem', fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', background: '#e2e8f0', color: '#334155', fontWeight: 'normal' }}>
                  via {msg.provider_used}
                </span>
              )}
            </span>
            <span>{msg.created_at || ''}</span>
          </div>

          {/* Attached or generated image if any */}
          {msg.image_url && (
            <div style={{ marginBottom: '0.6rem' }}>
              <img
                src={msg.image_url}
                alt="Chat Attachment"
                style={{ maxWidth: '100%', maxHeight: '350px', borderRadius: '8px', display: 'block' }}
              />
              <div style={{ marginTop: '0.3rem' }}>
                <a
                  href={msg.image_url}
                  download="image.png"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ fontSize: '0.75rem', color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                >
                  💾 Save / Open Full Image
                </a>
              </div>
            </div>
          )}

          {/* Crisis Banner if triggered */}
          {msg.crisis_flag && (
            <CrisisAlert />
          )}

          {/* Text Content */}
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {msg.content}
          </div>

          {/* Sources and citations */}
          {msg.sources && msg.sources.length > 0 && (
            <SourcesView sources={msg.sources} />
          )}

          {/* Audio Response Player */}
          {msg.role === 'assistant' && (msg.audio_base64 || msg.content) && (
            <AudioPlayer audioBase64={msg.audio_base64} textContent={msg.content} />
          )}
        </div>
      ))}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="message-bubble message-assistant">
          <div className="message-header">
            <span>🤖 Assistant</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#64748b' }}>
            <span>Thinking...</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
