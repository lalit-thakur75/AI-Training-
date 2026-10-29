import React, { useState, useEffect } from 'react';
import {
  fetchDocuments,
  fetchDocumentVersions,
  updateDocumentContent,
  aiEditDocument,
  uploadDocument
} from '../services/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function DocumentWorkspace({ onClose, onDocumentUpdated }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [content, setContent] = useState('');
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aiPreview, setAiPreview] = useState(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  const loadDocuments = async () => {
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDocId) {
        selectDocument(docs[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const selectDocument = async (docId) => {
    setSelectedDocId(docId);
    setAiPreview(null);
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/documents/${docId}`);
      const data = await res.json();
      setContent(data.content || '');

      const vers = await fetchDocumentVersions(docId);
      setVersions(vers);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      setLoading(true);
      setStatusMsg('Uploading and indexing for RAG...');
      const uploaded = await uploadDocument(file);
      await loadDocuments();
      await selectDocument(uploaded.id);
      setStatusMsg('Uploaded and indexed successfully!');
      if (onDocumentUpdated) onDocumentUpdated();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAiAction = async (action) => {
    if (!selectedDocId) return;
    try {
      setLoading(true);
      setStatusMsg(`Generating AI ${action}...`);
      const res = await aiEditDocument(selectedDocId, action, customPrompt);
      setAiPreview(res.proposed_content);
      setStatusMsg('AI proposal generated. Review and apply or discard.');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAiEdit = () => {
    if (aiPreview) {
      setContent(aiPreview);
      setAiPreview(null);
      setStatusMsg('Applied AI proposal to editor. Click "Save New Version" to commit.');
    }
  };

  const handleSaveVersion = async () => {
    if (!selectedDocId) return;
    try {
      setLoading(true);
      setStatusMsg('Saving new version and re-indexing RAG...');
      await updateDocumentContent(
        selectedDocId,
        content,
        `Updated manually / via AI`
      );
      await selectDocument(selectedDocId);
      setStatusMsg('New version saved and vector index updated!');
      if (onDocumentUpdated) onDocumentUpdated();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const activeDoc = documents.find((d) => d.id === selectedDocId);
    const filename = activeDoc ? activeDoc.filename.replace(/\.[^/.]+$/, "") + "_v_current.txt" : "document.txt";
    const element = document.createElement("a");
    const file = new Blob([content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="document-panel">
      <div className="workspace-header">
        <span className="workspace-title">📄 Document Workspace</span>
        <button className="btn-action" onClick={onClose} title="Close workspace">✕</button>
      </div>

      <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
          <select
            value={selectedDocId}
            onChange={(e) => selectDocument(e.target.value)}
            style={{ flex: 1, padding: '0.4rem', borderRadius: '4px', border: '1px solid #cbd5e1' }}
          >
            {documents.length === 0 && <option value="">No documents uploaded</option>}
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} (v{d.current_version})
              </option>
            ))}
          </select>
          <label className="btn-action" style={{ cursor: 'pointer', margin: 0 }}>
            + Upload
            <input
              type="file"
              accept=".txt,.pdf,.docx"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </label>
        </div>

        {versions.length > 0 && (
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Versions: {versions.map((v) => `v${v.version_number}`).join(', ')}
          </div>
        )}
      </div>

      {statusMsg && (
        <div style={{ padding: '0.4rem 1rem', fontSize: '0.75rem', background: '#e0f2fe', color: '#0369a1' }}>
          ℹ️ {statusMsg}
        </div>
      )}

      <div className="workspace-editor">
        {/* AI Action toolbar */}
        <div className="workspace-actions">
          <button
            className="btn-action"
            onClick={() => handleAiAction('summarize')}
            disabled={loading || !selectedDocId}
          >
            ✨ Summarize
          </button>
          <button
            className="btn-action"
            onClick={() => handleAiAction('grammar')}
            disabled={loading || !selectedDocId}
          >
            📝 Fix Grammar
          </button>
          <button
            className="btn-action"
            onClick={() => handleAiAction('expand')}
            disabled={loading || !selectedDocId}
          >
            🔍 Expand
          </button>
          <button
            className="btn-action"
            onClick={handleDownload}
            disabled={!content}
          >
            💾 Download .TXT
          </button>
          <button
            className="btn-action btn-primary-action"
            onClick={handleSaveVersion}
            disabled={loading || !selectedDocId}
          >
            ✓ Save New Version
          </button>
        </div>

        {/* AI Proposed Changes Preview Diff */}
        {aiPreview && (
          <div style={{
            background: '#fefce8',
            border: '1px solid #fef08a',
            padding: '0.75rem',
            borderRadius: '6px',
            fontSize: '0.85rem'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '0.3rem', color: '#854d0e' }}>
              💡 Proposed AI Changes:
            </div>
            <div style={{ maxHeight: '120px', overflowY: 'auto', whiteSpace: 'pre-wrap', color: '#422006' }}>
              {aiPreview}
            </div>
            <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn-action btn-primary-action" onClick={handleApplyAiEdit}>
                Accept & Replace
              </button>
              <button className="btn-action" onClick={() => setAiPreview(null)}>
                Discard
              </button>
            </div>
          </div>
        )}

        {/* Editor Content Area */}
        <textarea
          className="workspace-textarea"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={
            selectedDocId
              ? "Document text is loaded here. You can manually edit or use AI tools..."
              : "Upload or create a document to begin editing..."
          }
          disabled={!selectedDocId}
        />
      </div>
    </div>
  );
}
