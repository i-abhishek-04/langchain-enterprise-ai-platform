// Enterprise API Client Service
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

let accessToken = null;
let unauthorizedHandler = null;

export function setApiAccessToken(token) {
  accessToken = token;
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

async function apiRequest(path, options = {}, requireAuth = true) {
  const headers = new Headers(options.headers || {});
  if (requireAuth && accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (requireAuth && response.status === 401) {
    setApiAccessToken(null);
    unauthorizedHandler?.();
  }
  return response;
}

async function readApiError(response, fallback) {
  const error = await response.json().catch(() => ({}));
  const detail = error.detail;
  throw new Error(typeof detail === 'string' ? detail : fallback);
}

async function authenticate(path, credentials) {
  const response = await apiRequest(
    path,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    },
    false
  );
  if (!response.ok) await readApiError(response, 'Authentication failed.');
  return await response.json();
}

export function loginApi(credentials) {
  return authenticate('/auth/login', credentials);
}

export function registerApi(credentials) {
  return authenticate('/auth/register', credentials);
}

export async function uploadDocumentApi(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiRequest('/documents/upload', {
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
    const response = await apiRequest('/documents');
    if (!response.ok) return [];
    const data = await response.json();
    return data.documents || [];
  } catch (e) {
    return [];
  }
}

export async function deleteDocumentApi(docId) {
  const response = await apiRequest(`/documents/${docId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete document');
  return await response.json();
}

export async function runMultiAgentChatApi(payload) {
  try {
    const response = await apiRequest('/chat', {
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
    const response = await apiRequest('/metrics');
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    return null;
  }
}

export async function fetchAdminStatsApi() {
  try {
    const response = await apiRequest('/admin/stats');
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    return null;
  }
}
