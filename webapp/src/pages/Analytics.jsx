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

function timeAgo(ts) {
  if (!ts) return '—'
  const d = new Date(ts + 'Z')
  const sec = Math.floor((Date.now() - d) / 1000)
  if (sec < 60) return `${sec}s ago`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`
  return `${Math.floor(sec / 86400)}d ago`
}

function BenchSummary({ data, nav }) {
  const { overall, baseline, with_rag, by_project, by_provider, rag_examples, recent_runs } = data
  return (
    <div>
      <div className="section-label" style={{ marginBottom: 12 }}>Benchmark</div>

      <div className="stat-row" style={{ marginBottom: 20 }}>
        <Stat label="Runs" value={overall.runs} />
        <Stat label="Resolved (S)" value={overall.resolved}
              color={overall.resolved > 0 ? 'var(--green-fg)' : 'var(--text-2)'}
              sub={`${overall.resolved_rate}% of runs`} />
        <Stat label="Detected" value={overall.detected}
              sub={`${overall.detection_rate}% of runs`} />
      </div>

      <div className="section-label" style={{ marginBottom: 10 }}>Baseline vs RAG</div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { title: 'Baseline', bucket: baseline, hint: 'use_rag = false' },
          { title: 'With RAG', bucket: with_rag, hint: 'use_rag = true' },
        ].map(({ title, bucket, hint }) => (
          <div key={title} className="card" style={{ flex: 1, minWidth: 160, padding: '14px 16px' }}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>{title}</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10 }}>{hint}</div>
            {!bucket.runs ? (
              <p style={{ color: 'var(--text-3)', fontSize: 12, margin: 0 }}>No runs yet.</p>
            ) : (
              <>
                <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 4 }}>
                  <span style={{ color: 'var(--text)' }}>{bucket.runs}</span> runs
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 4 }}>
                  Resolved: <span style={{ color: bucket.resolved > 0 ? 'var(--green-fg)' : 'var(--text-3)', fontWeight: 600 }}>{bucket.resolved_rate}%</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-2)' }}>
                  Detected: <span style={{ fontWeight: 600 }}>{bucket.detection_rate}%</span>
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 0, marginBottom: 16 }}>
        <div className="card-header"><h3>By project</h3></div>
        <div style={{ padding: by_project.length ? 0 : 16 }}>
          <BreakdownTable rows={by_project} labelKey="project" labelTitle="Project" />
        </div>
      </div>

      <div className="card" style={{ padding: 0, marginBottom: 16 }}>
        <div className="card-header"><h3>By provider</h3></div>
        <div style={{ padding: by_provider.length ? 0 : 16 }}>
          <BreakdownTable rows={by_provider} labelKey="provider" labelTitle="Provider" />
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div className="card-header"><h3>Recent benchmark runs</h3></div>
        {recent_runs.length === 0 ? (
          <p style={{ padding: '24px 16px', color: 'var(--text-3)', fontSize: 13 }}>No benchmark runs yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Instance</th>
                <th>Provider</th>
                <th style={{ textAlign: 'center' }}>RAG</th>
                <th style={{ textAlign: 'center' }}>F→P</th>
                <th style={{ textAlign: 'center' }}>F→F</th>
                <th style={{ textAlign: 'center' }}>S</th>
              </tr>
            </thead>
            <tbody>
              {recent_runs.map(r => (
                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{r.benchmark_id || `#${r.id}`}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-3)' }}>{r.provider || '—'}</td>
                  <td style={{ textAlign: 'center' }}>
                    {r.use_rag ? <span style={{ color: 'var(--green-fg)' }}>✓</span> : <span style={{ color: 'var(--text-3)' }}>—</span>}
                  </td>
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
    </div>
  )
}

function UserSummary({ data, nav }) {
  const { summary, recent_runs } = data
  return (
    <div>
      <div className="section-label" style={{ marginBottom: 12 }}>User Runs</div>

      <div className="stat-row" style={{ marginBottom: 20 }}>
        <Stat label="Total Runs" value={summary.runs} />
        <Stat label="Tests Passed" value={summary.tests_passed} color="var(--green-fg)" />
        <Stat label="Tests Failed" value={summary.tests_failed}
              color={summary.tests_failed > 0 ? 'var(--red-fg)' : 'var(--text-2)'} />
        <Stat label="Avg Coverage" value={summary.runs ? `${summary.avg_coverage}%` : '—'} />
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div className="card-header"><h3>Recent user runs</h3></div>
        {recent_runs.length === 0 ? (
          <p style={{ padding: '24px 16px', color: 'var(--text-3)', fontSize: 13 }}>No user runs yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Repository</th>
                <th>Provider</th>
                <th style={{ textAlign: 'center' }}>RAG</th>
                <th style={{ textAlign: 'center' }}>Pass</th>
                <th style={{ textAlign: 'center' }}>Fail</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {recent_runs.map(r => (
                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                  <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                    {r.repo_url}
                  </td>
                  <td style={{ fontSize: 12, color: 'var(--text-3)' }}>{r.provider || '—'}</td>
                  <td style={{ textAlign: 'center' }}>
                    {r.use_rag ? <span style={{ color: 'var(--green-fg)' }}>✓</span> : <span style={{ color: 'var(--text-3)' }}>—</span>}
                  </td>
                  <td style={{ textAlign: 'center', color: 'var(--green-fg)' }}>{r.tests_passed ?? '—'}</td>
                  <td style={{ textAlign: 'center', color: r.tests_failed > 0 ? 'var(--red-fg)' : 'var(--text-3)' }}>{r.tests_failed ?? '—'}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-3)' }}>{timeAgo(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const nav = useNavigate()

  useEffect(() => {
    setData(null)
    setError('')
    getAnalyticsSummary('both').then(setData).catch(e => setError(e.message))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {!data && !error && <p style={{ color: 'var(--text-3)' }}>Loading…</p>}

      {data && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 24 }}>
          <BenchSummary data={data.mode === 'both' ? data.benchmark : data} nav={nav} />
          <UserSummary data={data.mode === 'both' ? data.user : { summary: {}, recent_runs: [] }} nav={nav} />
        </div>
      )}
    </div>
  )
}
