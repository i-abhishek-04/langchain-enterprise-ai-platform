import React, { useState } from 'react';
import Header from './components/Header';
import Playground from './components/Playground';
import DocumentUpload from './components/DocumentUpload';
import AgentGraphVisualizer from './components/AgentGraphVisualizer';
import AdminDashboard from './components/AdminDashboard';
import ChainVisualizer from './components/ChainVisualizer';
import PromptLibrary from './components/PromptLibrary';
import ProviderModal from './components/ProviderModal';
import { PROVIDERS } from './services/aiProviders';

export default function App() {
  const [activeTab, setActiveTab] = useState('playground'); // 'playground' | 'rag' | 'agents' | 'admin' | 'visualizer' | 'library'
  const [selectedProvider, setSelectedProvider] = useState('groq');
  const [selectedModel, setSelectedModel] = useState(PROVIDERS.groq.models[0].id);

  // Load API keys from localStorage safely
  const [apiKeys, setApiKeys] = useState(() => {
    try {
      const saved = localStorage.getItem('langchain_free_ai_keys');
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      return {};
    }
  });

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activePromptTemplate, setActivePromptTemplate] = useState(null);

  const handleSaveKey = (providerId, key) => {
    const updated = { ...apiKeys, [providerId]: key };
    setApiKeys(updated);
    try {
      localStorage.setItem('langchain_free_ai_keys', JSON.stringify(updated));
    } catch (e) {}
  };

  const handleLoadTemplate = (template) => {
    setActivePromptTemplate(template);
    setActiveTab('playground');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Header Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedProvider={selectedProvider}
        setSelectedProvider={setSelectedProvider}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        onOpenSettings={() => setIsSettingsOpen(true)}
        apiKeys={apiKeys}
      />

      {/* Main View Area */}
      <main style={{ flex: 1 }}>
        {activeTab === 'playground' && (
          <Playground
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            apiKeys={apiKeys}
            onOpenSettings={() => setIsSettingsOpen(true)}
            activePromptTemplate={activePromptTemplate}
          />
        )}

        {activeTab === 'rag' && (
          <DocumentUpload
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            apiKeys={apiKeys}
          />
        )}

        {activeTab === 'agents' && (
          <AgentGraphVisualizer />
        )}

        {activeTab === 'admin' && (
          <AdminDashboard />
        )}

        {activeTab === 'visualizer' && (
          <ChainVisualizer
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
          />
        )}

        {activeTab === 'library' && (
          <PromptLibrary onLoadTemplate={handleLoadTemplate} />
        )}
      </main>

      {/* Provider Keys Modal */}
      <ProviderModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiKeys={apiKeys}
        onSaveKey={handleSaveKey}
      />

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '16px',
        fontSize: '0.78rem',
        color: 'var(--text-muted)',
        borderTop: '1px solid var(--border-color)',
        background: 'rgba(0,0,0,0.2)'
      }}>
        Document Q&amp;A Playground • FastAPI, LangGraph, LangChain, and Qdrant
      </footer>

    </div>
  );
}
