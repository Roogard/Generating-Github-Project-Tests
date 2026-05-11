import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFeaturedBatch } from '../api.js'

function fmtElapsed(s) {
  if (s == null) return '—'
  if (s < 60) return `${s.toFixed(1)}s`
  const m = Math.floor(s / 60)
  const sec = Math.round(s - m * 60)
  return `${m}m ${sec}s`
}

function ResolvedBadge({ resolved }) {
  return resolved
    ? <span className="chip chip-pass">resolved</span>
    : <span className="chip chip-fail">unresolved</span>
}

export default function Database() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getFeaturedBatch().then(setData).catch(e => setError(e.message))
  }, [])

  if (error) return (
    <div className="page"><div className="alert alert-error">{error}</div></div>
  )
  if (!data) return (
    <div className="page"><p style={{ color: 'var(--text-3)' }}>Loading...</p></div>
  )

  const { summary, instances } = data

  return (
    <div className="page">

      <div className="page-header" style={{ borderBottom: '0.5px solid #8B6914', paddingBottom: 20, marginBottom: 24 }}>
        <div>
          <h1 className="page-title" style={{ color: '#E8C97A' }}>Database</h1>
          <div className="page-sub">
            SWT-Bench Lite &nbsp;·&nbsp; {summary.model} &nbsp;·&nbsp; {summary.preset} preset &nbsp;·&nbsp; {summary.date}
          </div>
        </div>
        <span style={{ fontSize: 10, letterSpacing: '0.2em', color: '#8B6914', textTransform: 'uppercase', alignSelf: 'flex-end' }}>
          Benchmark Results
        </span>
      </div>

      <div className="stat-row">
        {/* Resolved — gold accent as primary metric */}
        <div className="stat-card" style={{ borderColor: '#8B6914' }}>
          <div className="stat-label">Resolved</div>
          <div className="stat-value" style={{ color: '#C9A84C' }}>
            {summary.resolved}
            <span style={{ fontSize: 16, color: 'var(--text-3)', fontWeight: 500 }}> / {summary.total}</span>
          </div>
          <div className="stat-sub">{summary.resolved_rate}% resolution rate</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Detected</div>
          <div className="stat-value">{summary.detected}</div>
          <div className="stat-sub">{summary.detection_rate}% bug-detection rate</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">F→P <span style={{ color: '#8B6914' }}>(good)</span></div>
          <div className="stat-value" style={{ color: 'var(--green-fg)' }}>{summary.f2p}</div>
          <div className="stat-sub">tests that catch the bug</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">F→F</div>
          <div className="stat-value" style={{ color: summary.f2f > 0 ? 'var(--red-fg)' : 'var(--text)' }}>{summary.f2f}</div>
          <div className="stat-sub">spurious failures</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">P→F</div>
          <div className="stat-value" style={{ color: summary.p2f > 0 ? 'var(--red-fg)' : 'var(--text)' }}>{summary.p2f}</div>
          <div className="stat-sub">regressions</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">P→P</div>
          <div className="stat-value">{summary.p2p}</div>
          <div className="stat-sub">neutral</div>
        </div>
      </div>

      <div className="card" style={{ padding: 0, borderColor: '#2a2310' }}>
        <div className="card-header" style={{ borderBottomColor: '#2a2310' }}>
          <h3>
            Issues &nbsp;
            <span style={{ color: 'var(--text-3)', fontWeight: 400 }}>{instances.length} runs</span>
          </h3>
          <span style={{ fontSize: 11, letterSpacing: '0.12em', color: '#8B6914', textTransform: 'uppercase' }}>
            click any row for full detail
          </span>
        </div>
        <table>
          <thead>
            <tr>
              <th style={{ color: '#8B6914' }}>Instance</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>F→P</th>
              <th style={{ textAlign: 'right' }}>F→F</th>
              <th style={{ textAlign: 'right' }}>P→F</th>
              <th style={{ textAlign: 'right' }}>P→P</th>
              <th style={{ textAlign: 'right' }}>Elapsed</th>
            </tr>
          </thead>
          <tbody>
            {instances.map(inst => (
              <tr key={inst.id} className="clickable">
                <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>
                  <Link to={`/runs/${inst.id}`} style={{ color: '#C9A84C' }}>
                    {inst.benchmark_id}
                  </Link>
                </td>
                <td><ResolvedBadge resolved={inst.resolved} /></td>
                <td style={{ textAlign: 'right', color: inst.f2p > 0 ? 'var(--green-fg)' : 'var(--text-3)' }}>{inst.f2p}</td>
                <td style={{ textAlign: 'right', color: inst.f2f > 0 ? 'var(--red-fg)' : 'var(--text-3)' }}>{inst.f2f}</td>
                <td style={{ textAlign: 'right', color: inst.p2f > 0 ? 'var(--red-fg)' : 'var(--text-3)' }}>{inst.p2f}</td>
                <td style={{ textAlign: 'right', color: 'var(--text-3)' }}>{inst.p2p}</td>
                <td style={{ textAlign: 'right', color: 'var(--text-3)', fontFamily: 'var(--mono)', fontSize: 12 }}>
                  {fmtElapsed(inst.elapsed_seconds)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  )
}