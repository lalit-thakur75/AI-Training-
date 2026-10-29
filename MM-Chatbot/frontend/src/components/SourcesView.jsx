import React, { useState } from 'react';

export default function SourcesView({ sources }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-card">
      <div
        className="sources-title"
        style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}
        onClick={() => setExpanded(!expanded)}
      >
        <span>📚 Sources & References ({sources.length})</span>
        <span>{expanded ? '▲ Hide' : '▼ View'}</span>
      </div>

      {expanded && (
        <div style={{ marginTop: '0.4rem' }}>
          {sources.map((src, idx) => (
            <div key={idx} className="source-item" style={{ flexDirection: 'column', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: src.source_type === 'web' ? '#dbeafe' : '#e0e7ff',
                  color: src.source_type === 'web' ? '#1e40af' : '#3730a3'
                }}>
                  {src.source_type === 'web' ? '🌐 Web' : '📄 Document'}
                </span>
                {src.source_type === 'web' ? (
                  <a href={src.url_or_file} target="_blank" rel="noopener noreferrer">
                    {src.title}
                  </a>
                ) : (
                  <strong style={{ color: '#1e293b' }}>{src.title}</strong>
                )}
              </div>
              {src.snippet && (
                <div style={{
                  fontSize: '0.75rem',
                  color: '#475569',
                  marginTop: '0.2rem',
                  background: '#ffffff',
                  padding: '0.3rem 0.5rem',
                  borderRadius: '4px',
                  border: '1px solid #e2e8f0',
                  width: '100%'
                }}>
                  "{src.snippet}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
