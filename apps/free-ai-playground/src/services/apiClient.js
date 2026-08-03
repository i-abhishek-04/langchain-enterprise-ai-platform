// Enterprise API Client Service
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function uploadDocumentApi(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Document upload failed.');
  }
  return await response.json();
}

export async function fetchDocumentsApi() {
  try {
    const response = await fetch(`${API_BASE_URL}/documents`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.documents || [];
  } catch (e) {
    return [];
  }
}

export async function deleteDocumentApi(docId) {
  const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete document');
  return await response.json();
}

export async function runMultiAgentChatApi(payload) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'API Chat failed');
    }
    return await response.json();
  } catch (e) {
    throw e;
  }
}

export async function fetchMetricsApi() {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics`);
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    return null;
  }
}

export async function fetchAdminStatsApi() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/stats`);
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    return null;
  }
}
