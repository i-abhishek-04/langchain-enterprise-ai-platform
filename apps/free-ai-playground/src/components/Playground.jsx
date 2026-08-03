import React, { useState } from 'react';
import { Play, Copy, Check, Sparkles, Clock, Zap, Cpu, Code2, RefreshCw } from 'lucide-react';
import { streamCompletion, PROVIDERS } from '../services/aiProviders';

export default function Playground({
  selectedProvider,
  selectedModel,
  apiKeys,
  onOpenSettings,
  activePromptTemplate
}) {
  const [systemPrompt, setSystemPrompt] = useState(
    activePromptTemplate?.systemPrompt || 'You are an expert AI assistant specializing in LangChain, Python, and modern software design.'
  );
  const [userPrompt, setUserPrompt] = useState(
    activePromptTemplate?.userPrompt || 'Explain how LangChain Expression Language (LCEL) chains prompt templates, models, and output parsers together with a simple Python code example.'
  );
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);

  const [output, setOutput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showCodeExport, setShowCodeExport] = useState(false);

  const providerConfig = PROVIDERS[selectedProvider];
  const apiKey = apiKeys[selectedProvider] || '';

  const handleGenerate = async () => {
    if (!userPrompt.trim()) return;
    setIsGenerating(true);
    setOutput('');
    setErrorMsg(null);
    setMetrics(null);

    await streamCompletion({
      providerId: selectedProvider,
      modelId: selectedModel,
      apiKey,
      systemPrompt,
      userPrompt,
      temperature,
      maxTokens,
      onChunk: (chunkText) => {
        setOutput(chunkText);
      },
      onFinish: (resultMetrics) => {
        setIsGenerating(false);
        setMetrics(resultMetrics);
      },
      onError: (errMsg) => {
        setIsGenerating(false);
        setErrorMsg(errMsg);
      }
    });
  };

  const handleCopyOutput = () => {
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const generatedLangChainSnippet = `from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# Provider: ${providerConfig.name} (${selectedModel})

system_message = """${systemPrompt.replace(/"/g, '\\"')}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("user", "{input_query}")
])

# Initialize model (Free Tier)
# model = ChatGroq(model="${selectedModel}", temperature=${temperature})

chain = prompt | model | StrOutputParser()

response = chain.invoke({"input_query": "${userPrompt.replace(/"/g, '\\"')}"})
print(response)
`;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', padding: '24px' }}>
      
      {/* Left Column: Config & Input Prompts */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Model & Config Bar */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={18} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '0.95rem' }}>Active Engine Settings</h3>
            </div>
            <span className="badge badge-blue">{providerConfig.name}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Temperature ({temperature})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-blue)' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Max Tokens ({maxTokens})
              </label>
              <input
                type="range"
                min="100"
                max="4000"
                step="100"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-purple)' }}
              />
            </div>
          </div>
        </div>

        {/* System Prompt */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
            System Prompt (Role Context):
          </label>
          <textarea
            className="textarea-field font-mono"
            rows={3}
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Define instructions for the model..."
          />
        </div>

        {/* User Prompt */}
        <div className="glass-panel" style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
            User Input Query:
          </label>
          <textarea
            className="textarea-field font-mono"
            style={{ flex: 1, minHeight: '120px', resize: 'vertical' }}
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            placeholder="Type your prompt here..."
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px' }}>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => setShowCodeExport(!showCodeExport)}
            >
              <Code2 size={14} /> {showCodeExport ? 'Hide Python Code' : 'Export Python Code'}
            </button>

            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={isGenerating || !userPrompt.trim()}
            >
              {isGenerating ? (
                <><RefreshCw size={16} className="pulse" /> Generating...</>
              ) : (
                <><Play size={16} /> Run Chain</>
              )}
            </button>
          </div>
        </div>

      </div>

      {/* Right Column: Output Panel & Metrics */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Generated Output */}
        <div className="glass-panel" style={{ padding: '18px', flex: 1, display: 'flex', flexDirection: 'column', minHeight: '400px' }}>
          
          {/* Output Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={16} color="var(--accent-purple)" />
              <h3 style={{ fontSize: '0.95rem' }}>Completion Output</h3>
              {isGenerating && <span className="badge badge-purple pulse">Streaming</span>}
            </div>

            {output && (
              <button className="btn btn-outline btn-sm" onClick={handleCopyOutput}>
                {copied ? <><Check size={14} color="var(--accent-emerald)" /> Copied</> : <><Copy size={14} /> Copy</>}
              </button>
            )}
          </div>

          {/* Error Banner if any */}
          {errorMsg && (
            <div style={{
              background: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 16px',
              color: '#fda4af',
              fontSize: '0.85rem',
              marginBottom: '12px'
            }}>
              <strong>Execution Error:</strong> {errorMsg}
              {providerConfig.apiKeyRequired && !apiKey && (
                <div style={{ marginTop: '8px' }}>
                  <button className="btn btn-primary btn-sm" onClick={onOpenSettings}>
                    Add Free Key for {providerConfig.name}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Code Export View or Live Output */}
          {showCodeExport ? (
            <pre style={{
              background: 'rgba(0,0,0,0.4)',
              padding: '14px',
              borderRadius: 'var(--radius-sm)',
              color: '#a7f3d0',
              fontSize: '0.82rem',
              overflowX: 'auto',
              flex: 1
            }}>
              <code>{generatedLangChainSnippet}</code>
            </pre>
          ) : (
            <div style={{
              flex: 1,
              whiteSpace: 'pre-wrap',
              fontSize: '0.9rem',
              color: output ? 'var(--text-primary)' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              lineHeight: '1.6',
              overflowY: 'auto'
            }}>
              {output || (isGenerating ? 'Connecting to free model backend...' : 'Click "Run Chain" to execute prompt through selected free AI provider.')}
            </div>
          )}

          {/* Performance Metrics Bar */}
          {metrics && (
            <div style={{
              display: 'flex',
              gap: '16px',
              marginTop: '14px',
              paddingTop: '12px',
              borderTop: '1px solid var(--border-color)',
              fontSize: '0.78rem',
              color: 'var(--text-secondary)'
            }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} color="var(--accent-cyan)" /> {metrics.durationMs} ms
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Zap size={14} color="var(--accent-amber)" /> {metrics.tokensPerSec} tokens/sec
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Cpu size={14} color="var(--accent-purple)" /> ~{metrics.totalTokens} tokens
              </span>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
