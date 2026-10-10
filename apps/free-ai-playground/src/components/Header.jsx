import React from 'react';
import { Key, Terminal, Network, BookOpen, Database, Activity, Bot } from 'lucide-react';
import { PROVIDERS } from '../services/aiProviders';

export default function Header({
  activeTab,
  setActiveTab,
  selectedProvider,
  setSelectedProvider,
  selectedModel,
  setSelectedModel,
  onOpenSettings,
  apiKeys
}) {
  const currentProviderConfig = PROVIDERS[selectedProvider];
  const hasKey = currentProviderConfig?.apiKeyRequired ? Boolean(apiKeys[selectedProvider]) : true;

  return (
    <header className="glass-panel" style={{ borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '12px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Brand / Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'var(--gradient-brand)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.4rem',
            boxShadow: 'var(--shadow-glow)'
          }}>
            🦜
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.25rem', color: 'var(--text-primary)' }}>AI Document Q&amp;A Playground</h1>
              <span className="badge badge-free">LangGraph + LangChain backend</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Document Q&amp;A, direct provider calls, and local prompt simulation
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', flexWrap: 'wrap' }}>
          <button
            className={`btn btn-sm ${activeTab === 'playground' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('playground')}
            style={{ border: 'none' }}
          >
            <Terminal size={14} /> Playground
          </button>

          <button
            className={`btn btn-sm ${activeTab === 'rag' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('rag')}
            style={{ border: 'none' }}
          >
            <Database size={14} /> Document Q&amp;A
          </button>

          <button
            className={`btn btn-sm ${activeTab === 'agents' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('agents')}
            style={{ border: 'none' }}
          >
            <Bot size={14} /> LangGraph Workflow
          </button>

          <button
            className={`btn btn-sm ${activeTab === 'admin' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('admin')}
            style={{ border: 'none' }}
          >
            <Activity size={14} /> Admin & Eval
          </button>

          <button
            className={`btn btn-sm ${activeTab === 'visualizer' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('visualizer')}
            style={{ border: 'none' }}
          >
            <Network size={14} /> LCEL Diagram
          </button>

          <button
            className={`btn btn-sm ${activeTab === 'library' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('library')}
            style={{ border: 'none' }}
          >
            <BookOpen size={14} /> Templates
          </button>
        </div>

        {/* Provider Controls & API Key Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          
          {/* Provider Select */}
          <select
            className="select-field"
            style={{ width: 'auto', minWidth: '140px', fontSize: '0.82rem' }}
            value={selectedProvider}
            onChange={(e) => {
              const pId = e.target.value;
              setSelectedProvider(pId);
              setSelectedModel(PROVIDERS[pId].models[0].id);
            }}
          >
            {Object.values(PROVIDERS).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          {/* Model Select */}
          <select
            className="select-field"
            style={{ width: 'auto', minWidth: '160px', fontSize: '0.82rem' }}
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {currentProviderConfig.models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>

          {/* API Key Modal Launcher */}
          <button
            className={`btn btn-sm ${hasKey ? 'btn-secondary' : 'btn-primary'}`}
            onClick={onOpenSettings}
            style={{ position: 'relative' }}
          >
            <Key size={14} /> Keys
            {!hasKey && (
              <span
                style={{
                  position: 'absolute',
                  top: '-4px',
                  right: '-4px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--accent-rose)',
                  boxShadow: '0 0 8px var(--accent-rose)'
                }}
              />
            )}
          </button>

        </div>

      </div>
    </header>
  );
}
