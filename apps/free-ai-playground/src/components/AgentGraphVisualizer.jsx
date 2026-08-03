import React, { useState } from 'react';
import { Network, Bot, ShieldCheck, Cpu, Search, CheckCircle2, Play, AlertCircle, RefreshCw } from 'lucide-react';
import { runMultiAgentChatApi } from '../services/apiClient';

export default function AgentGraphVisualizer() {
  const [testQuery, setTestQuery] = useState('What are the key integration providers available in the enterprise system?');
  const [isExecuting, setIsExecuting] = useState(false);
  const [agentLogs, setAgentLogs] = useState([]);
  const [activeStep, setActiveStep] = useState(0);
  const [finalResult, setFinalResult] = useState(null);

  const agents = [
    {
      id: 1,
      name: 'Agent 1: Document Processing Agent',
      icon: Bot,
      color: 'var(--accent-blue)',
      role: 'Parses input, cleans formatting, applies PII masking, and checks prompt injection guardrails.'
    },
    {
      id: 2,
      name: 'Agent 2: Retriever Agent',
      icon: Search,
      color: 'var(--accent-purple)',
      role: 'Queries Qdrant vector database for top-k relevant document chunks and ranks results.'
    },
    {
      id: 3,
      name: 'Agent 3: Reasoning Agent',
      icon: Cpu,
      color: 'var(--accent-cyan)',
      role: 'Generates comprehensive answer strictly constrained to retrieved document context using free LLM.'
    },
    {
      id: 4,
      name: 'Agent 4: Verification Agent',
      icon: ShieldCheck,
      color: 'var(--accent-emerald)',
      role: 'Evaluates citations, verifies faithfulness, checks hallucination score, and enforces final output safety.'
    }
  ];

  const handleRunPipeline = async () => {
    if (!testQuery.trim()) return;
    setIsExecuting(true);
    setAgentLogs([]);
    setFinalResult(null);
    setActiveStep(1);

    try {
      // Step 1: Doc Processing
      await new Promise(r => setTimeout(r, 400));
      setActiveStep(2);
      
      // Step 2: Retriever
      await new Promise(r => setTimeout(r, 400));
      setActiveStep(3);

      // Step 3: Reasoning & Step 4: Verification
      const res = await runMultiAgentChatApi({ query: testQuery });
      setActiveStep(4);
      setAgentLogs(res.agent_logs || []);
      setFinalResult(res);

    } catch (e) {
      setAgentLogs([`Error executing agent graph: ${e.message}`]);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Title */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Network size={24} color="var(--accent-purple)" />
          <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)' }}>LangGraph 4-Agent Orchestration Visualizer</h2>
          <span className="badge badge-purple">LangGraph Graph Flow</span>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Stateful multi-agent execution graph consisting of 4 autonomous agents working collaboratively to process, retrieve, reason, and verify answers.
        </p>
      </div>

      {/* Interactive Agent Run Bar */}
      <div className="glass-panel" style={{ padding: '18px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <input
          type="text"
          className="input-field"
          placeholder="Test query for 4-Agent LangGraph workflow..."
          value={testQuery}
          onChange={(e) => setTestQuery(e.target.value)}
        />
        <button className="btn btn-primary" onClick={handleRunPipeline} disabled={isExecuting || !testQuery.trim()}>
          {isExecuting ? <><RefreshCw size={16} className="pulse" /> Executing Graph...</> : <><Play size={16} /> Execute 4-Agent Graph</>}
        </button>
      </div>

      {/* Agents Flow Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
        {agents.map((agent) => {
          const Icon = agent.icon;
          const isActive = activeStep === agent.id;
          const isDone = activeStep > agent.id;

          return (
            <div
              key={agent.id}
              className="glass-panel"
              style={{
                padding: '16px',
                borderTop: `4px solid ${agent.color}`,
                boxShadow: isActive ? `0 0 20px ${agent.color}` : 'none',
                opacity: activeStep === 0 || isActive || isDone ? 1 : 0.6
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Icon size={18} color={agent.color} />
                <h4 style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>{agent.name}</h4>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {agent.role}
              </p>
              {isActive && <div style={{ fontSize: '0.7rem', color: agent.color, marginTop: '8px', fontWeight: 600 }}>▶ Active Step...</div>}
              {isDone && <div style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)', marginTop: '8px', fontWeight: 600 }}>✓ Completed</div>}
            </div>
          );
        })}
      </div>

      {/* Real-Time Agent Execution Logs */}
      {agentLogs.length > 0 && (
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.95rem', marginBottom: '12px', color: 'var(--text-primary)' }}>
            Real-Time Agent Execution Logs
          </h3>
          <div style={{ background: 'rgba(0,0,0,0.4)', padding: '14px', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#a7f3d0', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {agentLogs.map((log, i) => (
              <div key={i}>{log}</div>
            ))}
          </div>
        </div>
      )}

      {/* Verified Output Result */}
      {finalResult && (
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h3 style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>Verified Final Output</h3>
            <span className="badge badge-free">Confidence Score: {finalResult.confidence_score}</span>
          </div>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {finalResult.response}
          </div>
        </div>
      )}

    </div>
  );
}
