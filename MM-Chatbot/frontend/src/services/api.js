const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) {
      throw new Error(`Health check returned HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    return {
      status: 'offline',
      error: err.message,
      database: { connected: false },
      configured_providers: {}
    };
  }
}

export async function fetchProviderStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/providers/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { priority: [], providers: [] };
  }
}

export async function fetchProviderDiagnostics() {
  try {
    const res = await fetch(`${API_BASE_URL}/providers/diagnostics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function sendChatMessage(payload) {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with ${res.status}`);
  }
  return await res.json();
}

export async function generateImage(prompt, conversationId) {
  const res = await fetch(`${API_BASE_URL}/chat/generate-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, conversation_id: conversationId })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Image generation failed: ${res.status}`);
  }
  return await res.json();
}

export async function uploadVoiceMessage(formData) {
  const res = await fetch(`${API_BASE_URL}/chat/voice`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Voice upload error: ${res.status}`);
  }
  return await res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed: ${res.status}`);
  }
  return await res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE_URL}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return await res.json();
}

export async function fetchDocumentVersions(docId) {
  const res = await fetch(`${API_BASE_URL}/documents/${docId}/versions`);
  if (!res.ok) throw new Error('Failed to fetch document versions');
  return await res.json();
}

export async function updateDocumentContent(docId, content, changeSummary) {
  const res = await fetch(`${API_BASE_URL}/documents/${docId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, change_summary: changeSummary })
  });
  if (!res.ok) throw new Error('Failed to update document');
  return await res.json();
}

export async function aiEditDocument(docId, action, customInstruction) {
  const res = await fetch(`${API_BASE_URL}/documents/${docId}/ai-edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, custom_instruction: customInstruction })
  });
  if (!res.ok) throw new Error('Failed to process AI edit');
  return await res.json();
}

export async function fetchConversations() {
  const res = await fetch(`${API_BASE_URL}/chat/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return await res.json();
}

export async function fetchConversationHistory(convId) {
  const res = await fetch(`${API_BASE_URL}/chat/conversations/${convId}`);
  if (!res.ok) throw new Error('Failed to fetch conversation history');
  return await res.json();
}

export async function deleteConversation(convId) {
  const res = await fetch(`${API_BASE_URL}/chat/conversations/${convId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete conversation');
  return await res.json();
}
