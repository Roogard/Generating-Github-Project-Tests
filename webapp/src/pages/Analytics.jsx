import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAnalyticsSummary } from '../api.js'

function Stat({ label, value, sub, color }) {
  return (
    <div className="stat-card" style={{ flex: 1, minWidth: 130 }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: color || '#f8fafc' }}>{value ?? '—'}</div>
      {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function BenchCard({ title, bucket, hint }) {
  const empty = !bucket.runs
  return (
    <div className="card" style={{ flex: 1, minWidth: 280 }}>
      <h3 style={{ fontSize: 14, marginBottom: 4 }}>{title}</h3>
      {hint && <div style={{ fontSize: 11, color: '#64748b', marginBottom: 12 }}>{hint}</div>}
      {empty ? (
        <p style={{ color: '#64748b', fontSize: 13, margin: 0 }}>No runs yet.</p>
      ) : (
        <>
          <div className="stat-row" style={{ marginBottom: 10 }}>
            <Stat label="Runs" value={bucket.runs} />
            <Stat label="S (Resolved)" value={`${bucket.resolved}`}
                  color={bucket.resolved > 0 ? '#6ee7b7' : '#94a3b8'}
                  sub={`${bucket.resolved_rate}% of runs`} />
            <Stat label="Detected" value={bucket.detected}
                  sub={`${bucket.detection_rate}% of runs`} />
          </div>
          <div className="stat-row">
            <Stat label="Σ F→P" value={bucket.f2p} color="#6ee7b7" />
            <Stat label="Σ F→F" value={bucket.f2f} color={bucket.f2f > 0 ? '#fca5a5' : '#94a3b8'} />
            <Stat label="Σ P→F" value={bucket.p2f} color={bucket.p2f > 0 ? '#fca5a5' : '#94a3b8'} />
            <Stat label="Σ P→P" value={bucket.p2p} />
          </div>
        </>
      )}
    </div>
  )
}

function BreakdownTable({ rows, labelKey, labelTitle }) {
  if (!rows.length) return <p style={{ color: '#64748b', fontSize: 13 }}>No data yet.</p>
  return (
    <table>
      <thead>
        <tr>
          <th>{labelTitle}</th>
          <th style={{ textAlign: 'center' }}>Runs</th>
          <th style={{ textAlign: 'center' }}>Resolved</th>
          <th style={{ textAlign: 'center' }}>F→P</th>
          <th style={{ textAlign: 'center' }}>F→F</th>
          <th style={{ textAlign: 'center' }}>P→F</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => (
          <tr key={r[labelKey]}>
            <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{r[labelKey]}</td>
            <td style={{ textAlign: 'center' }}>{r.runs}</td>
            <td style={{ textAlign: 'center' }}>
              <span style={{ color: r.resolved > 0 ? '#6ee7b7' : '#64748b', fontWeight: 600 }}>
                {r.resolved}/{r.runs}
              </span>
              <div style={{ fontSize: 11, color: '#475569' }}>{r.resolved_rate}%</div>
            </td>
            <td style={{ textAlign: 'center', color: '#6ee7b7' }}>{r.f2p}</td>
            <td style={{ textAlign: 'center', color: r.f2f > 0 ? '#fca5a5' : '#64748b' }}>{r.f2f}</td>
            <td style={{ textAlign: 'center', color: r.p2f > 0 ? '#fca5a5' : '#64748b' }}>{r.p2f}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const nav = useNavigate()

  useEffect(() => {
    getAnalyticsSummary().then(setData).catch(e => setError(e.message))
  }, [])

  if (error) return <div className="page"><div className="alert alert-error">{error}</div></div>
  if (!data) return <div className="page"><p style={{ color: '#64748b' }}>Loading…</p></div>

  const { overall, baseline, with_rag, by_project, by_provider, rag_examples, recent_runs } = data

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Benchmark Interpreter</h1>
        <span style={{ fontSize: 13, color: '#64748b' }}>
          SWT-bench across QuixBugs runs
        </span>
      </div>

      <div className="stat-row" style={{ marginBottom: 24 }}>
        <Stat label="Benchmark Runs" value={overall.runs} />
        <Stat label="Resolved (S)" value={overall.resolved}
              color={overall.resolved > 0 ? '#6ee7b7' : '#94a3b8'}
              sub={`${overall.resolved_rate}% of runs`} />
        <Stat label="Detected" value={overall.detected}
              sub={`${overall.detection_rate}% of runs`} />
        <Stat label="Applicable (W)" value={overall.patch_applied}
              sub="patch applied cleanly" />
        <Stat label="RAG examples" value={rag_examples}
              sub="in ChromaDB" />
      </div>

      <h2 style={{ fontSize: 14, margin: '0 0 10px', color: '#94a3b8' }}>
        Base vs RAG
      </h2>
      <div style={{ display: 'flex', gap: 16, marginBottom: 28, flexWrap: 'wrap' }}>
        <BenchCard title="Baseline (no RAG)" bucket={baseline}
                   hint="use_rag = false" />
        <BenchCard title="With RAG" bucket={with_rag}
                   hint="use_rag = true" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid #334155' }}>
            <h3 style={{ fontSize: 14, margin: 0 }}>By project</h3>
          </div>
          <div style={{ padding: by_project.length ? 0 : 16 }}>
            <BreakdownTable rows={by_project} labelKey="project" labelTitle="Project" />
          </div>
        </div>

        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid #334155' }}>
            <h3 style={{ fontSize: 14, margin: 0 }}>By provider</h3>
          </div>
          <div style={{ padding: by_provider.length ? 0 : 16 }}>
            <BreakdownTable rows={by_provider} labelKey="provider" labelTitle="Provider" />
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid #334155' }}>
          <h3 style={{ fontSize: 14, margin: 0 }}>Recent benchmark runs</h3>
        </div>
        {recent_runs.length === 0 ? (
          <p style={{ padding: 32, textAlign: 'center', color: '#64748b' }}>
            No benchmark runs yet.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Instance</th>
                <th>Mode</th>
                <th>Provider</th>
                <th style={{ textAlign: 'center' }}>RAG</th>
                <th style={{ textAlign: 'center' }}>F→P</th>
                <th style={{ textAlign: 'center' }}>F→F</th>
                <th style={{ textAlign: 'center' }}>P→F</th>
                <th style={{ textAlign: 'center' }}>Resolved</th>
              </tr>
            </thead>
            <tbody>
              {recent_runs.map(r => (
                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                  <td style={{ fontFamily: 'monospace', fontSize: 13 }}>
                    {r.benchmark_id || `#${r.id}`}
                  </td>
                  <td style={{ fontSize: 12, color: '#64748b' }}>{r.mode}</td>
                  <td style={{ fontSize: 12, color: '#64748b' }}>{r.provider || '—'}</td>
                  <td style={{ textAlign: 'center' }}>
                    {r.use_rag ? <span style={{ color: '#6ee7b7' }}>✓</span> : <span style={{ color: '#475569' }}>—</span>}
                  </td>
                  <td style={{ textAlign: 'center', color: '#6ee7b7' }}>{r.f2p}</td>
                  <td style={{ textAlign: 'center', color: r.f2f > 0 ? '#fca5a5' : '#64748b' }}>{r.f2f}</td>
                  <td style={{ textAlign: 'center', color: r.p2f > 0 ? '#fca5a5' : '#64748b' }}>{r.p2f}</td>
                  <td style={{ textAlign: 'center' }}>
                    {r.resolved ? (
                      <span style={{ color: '#6ee7b7', fontWeight: 600 }}>YES</span>
                    ) : (
                      <span style={{ color: '#475569' }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
