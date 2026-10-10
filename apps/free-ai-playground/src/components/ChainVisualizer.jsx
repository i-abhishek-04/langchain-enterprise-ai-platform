import React from 'react';
import { ArrowRight, Box, MessageSquare, Cpu, CheckCircle2, Workflow, Database, Layers } from 'lucide-react';
import { PROVIDERS } from '../services/aiProviders';

export default function ChainVisualizer({ selectedProvider, selectedModel }) {
  const provider = PROVIDERS[selectedProvider];

  const steps = [
    {
      id: 'input',
      title: '1. User Input Query',
      type: 'Input Variable',
      icon: MessageSquare,
      color: 'var(--accent-blue)',
      details: '{ "input_query": "Your user prompt here" }'
    },
    {
      id: 'prompt',
      title: '2. Prompt Formatting',
      type: 'Illustrative step',
      icon: Box,
      color: 'var(--accent-cyan)',
      details: 'A LangChain ChatPromptTemplate can format system instructions and user input as messages.'
    },
    {
      id: 'model',
      title: `3. ${provider.name}`,
      type: `Provider or simulator (${selectedModel})`,
      icon: Cpu,
      color: 'var(--accent-purple)',
      details: `${provider.name}: this browser app calls configured providers directly; the local simulator does not call a model.`
    },
    {
      id: 'parser',
      title: '4. Text Output',
      type: 'Illustrative step',
      icon: Layers,
      color: 'var(--accent-amber)',
      details: 'A LangChain StrOutputParser can extract text from a model response.'
    },
    {
      id: 'output',
      title: '5. Final Output Result',
      type: 'Clean Output',
      icon: CheckCircle2,
      color: 'var(--accent-emerald)',
      details: 'Text shown in the playground output panel.'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      
      {/* Title */}
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Workflow size={24} color="var(--accent-blue)" />
          <h2 style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>Illustrative LCEL Flow</h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          This diagram is illustrative and does not execute an LCEL chain. The browser playground calls supported providers directly; the backend document Q&A endpoint uses LangChain LCEL for Groq.
        </p>
      </div>

      {/* Flow Cards Container */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '850px', margin: '0 auto' }}>
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <React.Fragment key={step.id}>
              
              <div className="glass-panel" style={{ padding: '20px', borderLeft: `4px solid ${step.color}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      padding: '8px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.05)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Icon size={20} color={step.color} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>{step.title}</h3>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{step.type}</span>
                    </div>
                  </div>
                </div>

                <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', marginTop: '8px', fontFamily: step.id === 'input' ? 'var(--font-mono)' : 'inherit' }}>
                  {step.details}
                </p>
              </div>

              {/* Arrow Connector */}
              {idx < steps.length - 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', margin: '-4px 0' }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-muted)'
                  }}>
                    ↓
                  </div>
                </div>
              )}

            </React.Fragment>
          );
        })}
      </div>

    </div>
  );
}
