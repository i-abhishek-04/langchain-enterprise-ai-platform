import React, { useState } from 'react';
import { X, ExternalLink, ShieldCheck, Check, Info } from 'lucide-react';
import { PROVIDERS } from '../services/aiProviders';

export default function ProviderModal({ isOpen, onClose, apiKeys, onSaveKey }) {
  if (!isOpen) return null;

  const [activeProvider, setActiveProvider] = useState('groq');
  const [keyInput, setKeyInput] = useState(apiKeys[activeProvider] || '');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const provider = PROVIDERS[activeProvider];

  const handleSave = () => {
    onSaveKey(activeProvider, keyInput.trim());
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-panel" style={{ padding: '24px' }} onClick={(e) => e.stopPropagation()}>
        
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={22} color="var(--accent-emerald)" />
            <h2 style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>Free Tier Provider Keys</h2>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose} style={{ padding: '4px 8px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Security Info Alert */}
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 14px',
          marginBottom: '20px',
          display: 'flex',
          gap: '10px',
          fontSize: '0.82rem',
          color: '#93c5fd'
        }}>
          <Info size={18} style={{ shrink: 0, marginTop: '2px' }} />
          <div>
            API Keys are stored securely in your browser's local storage (<strong>localStorage</strong>).
            They are sent directly to official provider APIs (Groq, Google, OpenRouter) and never stored on any intermediate server.
          </div>
        </div>

        {/* Provider Tabs */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '10px', marginBottom: '20px' }}>
          {Object.values(PROVIDERS).map((p) => {
            const isSelected = p.id === activeProvider;
            const hasKey = Boolean(apiKeys[p.id]);
            return (
              <button
                key={p.id}
                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => {
                  setActiveProvider(p.id);
                  setKeyInput(apiKeys[p.id] || '');
                }}
                style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}
              >
                {p.name}
                {hasKey && <Check size={12} color="var(--accent-emerald)" />}
              </button>
            );
          })}
        </div>

        {/* Selected Provider Key Input Form */}
        <div style={{ background: 'rgba(0,0,0,0.2)', padding: '18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>{provider.name}</h3>
            <span className="badge badge-purple">{provider.badge}</span>
          </div>

          <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            {provider.description}
          </p>

          {provider.apiKeyRequired ? (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                API Key for {provider.name}:
              </label>
              <input
                type="password"
                className="input-field"
                placeholder={`Enter your ${provider.name} API key...`}
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                style={{ marginBottom: '12px' }}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <a
                  href={provider.keyUrl}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: 'var(--accent-cyan)', fontSize: '0.82rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  Get Free API Key <ExternalLink size={12} />
                </a>

                <button className="btn btn-primary btn-sm" onClick={handleSave}>
                  {savedSuccess ? <><Check size={14} /> Saved!</> : 'Save Key'}
                </button>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--accent-emerald)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px', paddingTop: '8px' }}>
              <Check size={16} /> No API key needed for {provider.name}! Works out-of-the-box.
            </div>
          )}
        </div>

        <div style={{ marginTop: '20px', textAlign: 'right' }}>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Done
          </button>
        </div>

      </div>
    </div>
  );
}
