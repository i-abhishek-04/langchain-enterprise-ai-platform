import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, Clock, Zap, Database, BarChart3, RefreshCw, FileText, CheckCircle } from 'lucide-react';
import { fetchMetricsApi, fetchAdminStatsApi } from '../services/apiClient';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    const [s, m] = await Promise.all([fetchAdminStatsApi(), fetchMetricsApi()]);
    setStats(s);
    setMetrics(m);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Title */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <Activity size={24} color="var(--accent-emerald)" />
            <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)' }}>Enterprise AI Evaluation & Admin Dashboard</h2>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Real-time telemetry, PostgreSQL observability logs, guardrail flags, token analytics, and hallucination scores.
          </p>
        </div>

        <button className="btn btn-outline btn-sm" onClick={loadData} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'pulse' : ''} /> Refresh Data
        </button>
      </div>

      {/* Metric Cards Row */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '16px' }}>
          
          <div className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid var(--accent-blue)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Total Queries</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats.total_queries_processed}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-emerald)', marginTop: '4px' }}>100% Free Tier</div>
          </div>

          <div className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid var(--accent-purple)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Avg Latency</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats.avg_latency_ms} ms</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', marginTop: '4px' }}>High Speed</div>
          </div>

          <div className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid var(--accent-emerald)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Active Documents</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats.active_documents}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>Indexed in Qdrant</div>
          </div>

          <div className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid var(--accent-rose)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Hallucinations / Flags</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
              {stats.hallucination_count} / {stats.guardrail_flags_count}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>Filtered by Verifier</div>
          </div>

          <div className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid var(--accent-cyan)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Active Users</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats.active_users}</div>
          </div>

          <div className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid var(--accent-amber)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Most Used Model</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats.most_used_model || 'No usage yet'}</div>
          </div>

        </div>
      )}
      {!loading && !stats && (
        <p style={{ color: 'var(--text-secondary)' }}>Admin statistics are currently unavailable.</p>
      )}

      {/* Observability Logs Table */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={18} color="var(--accent-cyan)" />
          PostgreSQL Telemetry & Observability Logs
        </h3>

        {metrics?.logs?.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>ID</th>
                  <th style={{ padding: '8px' }}>User Query</th>
                  <th style={{ padding: '8px' }}>Latency</th>
                  <th style={{ padding: '8px' }}>Confidence</th>
                  <th style={{ padding: '8px' }}>Citations</th>
                  <th style={{ padding: '8px' }}>Guardrail</th>
                </tr>
              </thead>
              <tbody>
                {metrics.logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>#{log.id}</td>
                    <td style={{ padding: '8px', color: 'var(--text-primary)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {log.user_query}
                    </td>
                    <td style={{ padding: '8px', color: 'var(--accent-cyan)' }}>{log.latency_ms} ms</td>
                    <td style={{ padding: '8px', color: 'var(--accent-emerald)' }}>{log.confidence_score}</td>
                    <td style={{ padding: '8px' }}>{log.citation_count} sources</td>
                    <td style={{ padding: '8px' }}>
                      {log.guardrail_flagged ? (
                        <span className="badge badge-purple">Flagged</span>
                      ) : (
                        <span className="badge badge-free">Passed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', padding: '12px 0' }}>
            No evaluation logs stored yet. Execute queries in the Playground or RAG manager to populate telemetry.
          </div>
        )}
      </div>

    </div>
  );
}
