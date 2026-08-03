import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, Trash2, CheckCircle2, Database, Search, Sparkles, AlertTriangle } from 'lucide-react';
import { uploadDocumentApi, fetchDocumentsApi, deleteDocumentApi, runMultiAgentChatApi } from '../services/apiClient';

export default function DocumentUpload({ selectedProvider, selectedModel, apiKeys }) {
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // RAG Search Tester State
  const [ragQuery, setRagQuery] = useState('');
  const [isRagSearching, setIsRagSearching] = useState(false);
  const [ragResult, setRagResult] = useState(null);

  const loadDocs = async () => {
    const docs = await fetchDocumentsApi();
    setDocuments(docs);
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setErrorMsg(null);
    setUploadStatus('Uploading & chunking document for Qdrant vector store...');

    try {
      const res = await uploadDocumentApi(file);
      setUploadStatus(`Successfully indexed '${res.document.filename}' into Qdrant! (${res.document.chunk_count} chunks created)`);
      loadDocs();
    } catch (err) {
      setErrorMsg(err.message || 'Document upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await deleteDocumentApi(docId);
      loadDocs();
    } catch (e) {
      setErrorMsg('Failed to delete document');
    }
  };

  const handleRagSearch = async () => {
    if (!ragQuery.trim()) return;
    setIsRagSearching(true);
    setRagResult(null);

    const apiKey = apiKeys ? (apiKeys[selectedProvider] || '') : '';

    try {
      const res = await runMultiAgentChatApi({
        query: ragQuery,
        provider_id: selectedProvider || 'groq',
        model_id: selectedModel || 'llama-3.3-70b-versatile',
        api_key: apiKey
      });
      setRagResult(res);
    } catch (err) {
      setErrorMsg('RAG Search failed: ' + err.message);
    } finally {
      setIsRagSearching(false);
    }
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Database size={24} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)' }}>Enterprise RAG & Qdrant Document Manager</h2>
          <span className="badge badge-free">Vector Ingestion</span>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Upload PDF, DOCX, TXT, or Markdown documents to chunk, embed, and index them into Qdrant vector database for citations & grounded retrieval.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        
        {/* Left Box: Upload & Document List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Upload Area */}
          <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', borderStyle: 'dashed', borderWidth: '2px', borderColor: 'var(--border-glowing)' }}>
            <UploadCloud size={40} color="var(--accent-blue)" style={{ margin: '0 auto 12px' }} />
            <h3 style={{ fontSize: '1rem', marginBottom: '6px' }}>Upload Enterprise Documents</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
              Supported Formats: <strong>PDF, DOCX, TXT, Markdown</strong> (Max 25MB)
            </p>

            <label className="btn btn-primary btn-sm" style={{ cursor: 'pointer', display: 'inline-flex' }}>
              Select Document
              <input type="file" accept=".pdf,.docx,.txt,.md,.markdown" onChange={handleFileUpload} style={{ display: 'none' }} disabled={isUploading} />
            </label>

            {uploadStatus && (
              <div style={{ marginTop: '12px', fontSize: '0.8rem', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                <CheckCircle2 size={14} /> {uploadStatus}
              </div>
            )}

            {errorMsg && (
              <div style={{ marginTop: '12px', fontSize: '0.8rem', color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                <AlertTriangle size={14} /> {errorMsg}
              </div>
            )}
          </div>

          {/* Document Table */}
          <div className="glass-panel" style={{ padding: '18px' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={16} color="var(--accent-purple)" />
              Indexed Documents ({documents.length})
            </h3>

            {documents.length === 0 ? (
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', padding: '16px 0', textAlign: 'center' }}>
                No documents uploaded yet. Upload a PDF or DOCX file to populate Qdrant vector store.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {documents.map((doc) => (
                  <div key={doc.id} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(0,0,0,0.25)',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)'
                  }}>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{doc.filename}</div>
                      <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>
                        {doc.chunk_count} chunks • {doc.file_type} • {doc.status}
                      </div>
                    </div>

                    <button className="btn btn-outline btn-sm" onClick={() => handleDelete(doc.id)} style={{ color: 'var(--accent-rose)', padding: '4px 8px' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Right Box: Live RAG Q&A Tester */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={18} color="var(--accent-emerald)" />
            <h3 style={{ fontSize: '0.95rem' }}>Grounded RAG Search & Citation Tester</h3>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              className="input-field"
              placeholder="Ask a question about your uploaded documents..."
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRagSearch()}
            />
            <button className="btn btn-primary btn-sm" onClick={handleRagSearch} disabled={isRagSearching || !ragQuery.trim()}>
              {isRagSearching ? 'Searching...' : 'Search RAG'}
            </button>
          </div>

          {/* RAG Answer & Citations */}
          {ragResult && (
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: 'var(--radius-md)', flex: 1, overflowY: 'auto' }}>
              
              {/* Bug 5 Warning Banner for Fallback Mode */}
              {ragResult.is_fallback_mode && (
                <div style={{
                  background: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid rgba(245, 158, 11, 0.35)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '10px 12px',
                  marginBottom: '12px',
                  fontSize: '0.8rem',
                  color: '#fcd34d',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <AlertTriangle size={16} color="var(--accent-amber)" />
                  <div>
                    <strong>⚠️ Fallback Mode Active:</strong> {ragResult.fallback_reason || 'Live LLM API key missing or unavailable. Showing raw retrieved context.'}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className={`badge ${ragResult.confidence_score >= 0.5 ? 'badge-free' : 'badge-purple'}`}>
                  Confidence: {ragResult.confidence_score}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Latency: {ragResult.metrics?.latency_ms} ms
                </span>
              </div>

              <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', marginBottom: '14px', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {ragResult.response}
              </div>

              {/* Citations Preview */}
              {ragResult.citations?.length > 0 && (
                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '6px' }}>
                    Source Citations ({ragResult.citations.length}):
                  </div>
                  {ragResult.citations.map((c, i) => (
                    <div key={i} style={{ background: 'rgba(59, 130, 246, 0.08)', padding: '8px 10px', borderRadius: '4px', fontSize: '0.75rem', marginBottom: '6px', color: '#93c5fd' }}>
                      <strong>[{c.filename}]</strong> {c.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
