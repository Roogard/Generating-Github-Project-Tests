import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAnalyticsSummary } from '../api.js'

function Stat({ label, value, sub, color }) {
  return (
    <div className="stat-card" style={{ flex: 1, minWidth: 110 }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: color || 'var(--text)' }}>{value ?? '—'}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

function BreakdownTable({ rows, labelKey, labelTitle }) {
  if (!rows.length) return <p style={{ color: 'var(--text-3)', fontSize: 13, padding: '12px 0' }}>No data yet.</p>
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
            <td style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{r[labelKey]}</td>
            <td style={{ textAlign: 'center' }}>{r.runs}</td>
            <td style={{ textAlign: 'center' }}>
              <span style={{ color: r.resolved > 0 ? 'var(--green-fg)' : 'var(--text-3)', fontWeight: 600 }}>
                {r.resolved}/{r.runs}
              </span>
              <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{r.resolved_rate}%</div>
            </td>
            <td style={{ textAlign: 'center', color: 'var(--green-fg)' }}>{r.f2p}</td>
            <td style={{ textAlign: 'center', color: r.f2f > 0 ? 'var(--red-fg)' : 'var(--text-3)' }}>{r.f2f}</td>
            <td style={{ textAlign: 'center', color: r.p2f > 0 ? 'var(--red-fg)' : 'var(--text-3)' }}>{r.p2f}</td>
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
    setData(null)
    setError('')
    getAnalyticsSummary().then(setData).catch(e => setError(e.message))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {!data && !error && <p style={{ color: 'var(--text-3)' }}>Loading…</p>}

      {data && (
        <>
          <div className="stat-row" style={{ marginBottom: 20 }}>
            <Stat label="Runs" value={data.overall.runs} />
            <Stat label="Resolved (S)" value={data.overall.resolved}
                  color={data.overall.resolved > 0 ? 'var(--green-fg)' : 'var(--text-2)'}
                  sub={`${data.overall.resolved_rate}% of runs`} />
            <Stat label="Detected" value={data.overall.detected}
                  sub={`${data.overall.detection_rate}% of runs`} />
          </div>

          <div className="card" style={{ padding: 0, marginBottom: 16 }}>
            <div className="card-header"><h3>By project</h3></div>
            <div style={{ padding: data.by_project.length ? 0 : 16 }}>
              <BreakdownTable rows={data.by_project} labelKey="project" labelTitle="Project" />
            </div>
          </div>

          <div className="card" style={{ padding: 0, marginBottom: 16 }}>
            <div className="card-header"><h3>By provider</h3></div>
            <div style={{ padding: data.by_provider.length ? 0 : 16 }}>
              <BreakdownTable rows={data.by_provider} labelKey="provider" labelTitle="Provider" />
            </div>
          </div>

          <div className="card" style={{ padding: 0 }}>
            <div className="card-header"><h3>Recent benchmark runs</h3></div>
            {data.recent_runs.length === 0 ? (
              <p style={{ padding: '24px 16px', color: 'var(--text-3)', fontSize: 13 }}>No benchmark runs yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Instance</th>
                    <th>Provider</th>
                    <th style={{ textAlign: 'center' }}>F→P</th>
                    <th style={{ textAlign: 'center' }}>F→F</th>
                    <th style={{ textAlign: 'center' }}>S</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_runs.map(r => (
                    <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                      <td style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{r.benchmark_id || `#${r.id}`}</td>
                      <td style={{ fontSize: 12, color: 'var(--text-3)' }}>{r.provider || '—'}</td>
                      <td style={{ textAlign: 'center', color: 'var(--green-fg)' }}>{r.f2p}</td>
                      <td style={{ textAlign: 'center', color: r.f2f > 0 ? 'var(--red-fg)' : 'var(--text-3)' }}>{r.f2f}</td>
                      <td style={{ textAlign: 'center' }}>
                        {r.resolved
                          ? <span className="chip chip-pass">S</span>
                          : <span style={{ color: 'var(--text-3)' }}>—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
