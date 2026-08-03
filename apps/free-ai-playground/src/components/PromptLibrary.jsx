import React from 'react';
import { BookOpen, ArrowRight, Code, FileText, Cpu, Database, Bot } from 'lucide-react';

export const PRESET_PROMPTS = [
  {
    id: 'lcel-demo',
    title: 'LCEL Chain Construction',
    category: 'LangChain Basics',
    icon: Code,
    color: 'var(--accent-blue)',
    systemPrompt: 'You are an expert LangChain Python engineer. Provide clear, minimal, and fully runnable code examples using modern LCEL syntax.',
    userPrompt: 'Show how to create a LangChain pipeline that takes a user topic, generates a 3-bullet point summary, and parses the result with StrOutputParser.'
  },
  {
    id: 'react-agent',
    title: 'ReAct Agent Logic Visualizer',
    category: 'Agents & Tools',
    icon: Bot,
    color: 'var(--accent-purple)',
    systemPrompt: 'You are a Reasoning and Acting (ReAct) agent loop simulator. Structure your output into Thought, Action, Action Input, and Final Answer.',
    userPrompt: 'Question: What is the current temperature in Tokyo and what should I wear there today?'
  },
  {
    id: 'structured-json',
    title: 'Structured Output Extractor',
    category: 'Data Extraction',
    icon: FileText,
    color: 'var(--accent-emerald)',
    systemPrompt: 'You are a strict data extraction AI. You MUST respond with ONLY valid JSON adhering to the specified schema, without markdown formatting or conversational text.',
    userPrompt: 'Extract entities from this text:\n"Acme Corp announced Q3 earnings of $14.2M led by CEO Sarah Connor in San Francisco on August 3rd, 2026."'
  },
  {
    id: 'rag-qa',
    title: 'RAG Contextual Q&A',
    category: 'Retrieval Augmented Generation',
    icon: Database,
    color: 'var(--accent-amber)',
    systemPrompt: 'You are a RAG assistant. Answer the user question based ONLY on the provided context retrieved from vector search. If the answer is not in the context, say "I cannot answer based on the provided documents."',
    userPrompt: 'Context: LangChain v1 introduces unified provider packages with uv support. Standardized integration testing is placed in libs/standard-tests.\n\nQuestion: Where are integration tests located in LangChain v1?'
  }
];

export default function PromptLibrary({ onLoadTemplate }) {
  return (
    <div style={{ padding: '24px' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <BookOpen size={24} color="var(--accent-purple)" />
          <h2 style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>Prompt & Chain Template Library</h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Click any template below to load system instructions, prompt patterns, and sample inputs directly into the interactive studio.
        </p>
      </div>

      {/* Grid of Templates */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '20px' }}>
        {PRESET_PROMPTS.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              className="glass-panel"
              style={{
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                borderTop: `3px solid ${item.color}`
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      padding: '8px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.05)',
                      display: 'flex'
                    }}>
                      <Icon size={20} color={item.color} />
                    </div>
                    <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>{item.title}</h3>
                  </div>
                  <span className="badge badge-blue" style={{ fontSize: '0.7rem' }}>{item.category}</span>
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                  <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '4px' }}>System Prompt Preview:</strong>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>"{item.systemPrompt.slice(0, 100)}..."</span>
                </div>
              </div>

              <button
                className="btn btn-outline btn-sm"
                onClick={() => onLoadTemplate(item)}
                style={{ width: '100%', marginTop: '12px', justifyContent: 'center' }}
              >
                Load Template into Playground <ArrowRight size={14} />
              </button>
            </div>
          );
        })}
      </div>

    </div>
  );
}
