import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

async function fetchSummary() {
  const res = await fetch('/api/analytics/summary')
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="stat-card" style={{ flex: 1, minWidth: 130 }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: color || '#f8fafc' }}>{value ?? '—'}</div>
      {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function CoverageBar({ dist }) {
  const total = dist.high + dist.medium + dist.low
  if (total === 0) return <p style={{ color: '#64748b', fontSize: 13 }}>No coverage data yet.</p>

  const pct = n => Math.round((n / total) * 100)
  return (
    <div>
      <div style={{ display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden', marginBottom: 10 }}>
        {dist.high > 0 && (
          <div style={{ width: `${pct(dist.high)}%`, background: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: '#fff', fontWeight: 600 }}>
            {pct(dist.high)}%
          </div>
        )}
        {dist.medium > 0 && (
          <div style={{ width: `${pct(dist.medium)}%`, background: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: '#fff', fontWeight: 600 }}>
            {pct(dist.medium)}%
          </div>
        )}
        {dist.low > 0 && (
          <div style={{ width: `${pct(dist.low)}%`, background: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: '#fff', fontWeight: 600 }}>
            {pct(dist.low)}%
          </div>
        )}
      </div>
      <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#94a3b8' }}>
        <span><span style={{ color: '#059669' }}>■</span> High ≥80%: {dist.high} tests</span>
        <span><span style={{ color: '#d97706' }}>■</span> Mid 50–80%: {dist.medium} tests</span>
        <span><span style={{ color: '#dc2626' }}>■</span> Low &lt;50%: {dist.low} tests</span>
      </div>
    </div>
  )
}

function RepoName(url) {
  try { return new URL(url).pathname.replace(/^\//, '').replace(/\.git$/, '') }
  catch { return url }
}

function elapsed(created, finished) {
  if (!created || !finished) return null
  const secs = Math.round((new Date(finished + 'Z') - new Date(created + 'Z')) / 1000)
  if (secs < 60) return `${secs}s`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ${secs % 60}s`
  return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const nav = useNavigate()

  useEffect(() => {
    fetchSummary().then(setData).catch(e => setError(e.message))
  }, [])

  if (error) return <div className="page"><div className="alert alert-error">{error}</div></div>
  if (!data) return <div className="page"><p style={{ color: '#64748b' }}>Loading analytics...</p></div>

  const {
    total_runs, total_functions, total_tests, total_passed, total_failed,
    pass_rate, avg_coverage_pct, coverage_distribution,
    total_bug_detections, runs_with_bugs, runs_with_fixes,
    rag_examples, recent_runs,
  } = data

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <span style={{ fontSize: 13, color: '#64748b' }}>Across all completed runs</span>
      </div>

      {/* ── Hero metrics ── */}
      <div className="stat-row" style={{ marginBottom: 28 }}>
        <StatCard label="Repos Analyzed" value={total_runs} />
        <StatCard label="Functions Tested" value={total_functions} />
        <StatCard label="Tests Generated" value={total_tests} />
        <StatCard label="Pass Rate" value={total_passed + total_failed > 0 ? `${pass_rate}%` : '—'} color={pass_rate >= 70 ? '#6ee7b7' : '#fca5a5'} sub={`${total_passed}p / ${total_failed}f`} />
        <StatCard label="Avg Coverage" value={avg_coverage_pct > 0 ? `${avg_coverage_pct}%` : '—'} />
        <StatCard label="Bugs Detected" value={total_bug_detections} color={total_bug_detections > 0 ? '#fca5a5' : '#6ee7b7'} sub={`in ${runs_with_bugs} run(s)`} />
      </div>

      {/* ── Two column section ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>

        {/* Coverage distribution */}
        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 14 }}>Test Coverage Distribution</h3>
          <CoverageBar dist={coverage_distribution} />
          {avg_coverage_pct > 0 && (
            <p style={{ marginTop: 14, fontSize: 13, color: '#94a3b8' }}>
              Average coverage across all generated test suites: <strong style={{ color: '#f8fafc' }}>{avg_coverage_pct}%</strong>
            </p>
          )}
        </div>

        {/* AI / RAG flywheel */}
        <div className="card">
          <h3 style={{ fontSize: 15, marginBottom: 14 }}>AI Test Memory (RAG)</h3>
          <div style={{ display: 'flex', gap: 16, marginBottom: 14 }}>
            <div className="stat-card" style={{ flex: 1 }}>
              <div className="stat-label">Examples Stored</div>
              <div className="stat-value">{rag_examples}</div>
            </div>
            <div className="stat-card" style={{ flex: 1 }}>
              <div className="stat-label">Fix Passes Run</div>
              <div className="stat-value">{runs_with_fixes}</div>
            </div>
          </div>
          <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>
            Each completed run stores successful test examples in ChromaDB. The LLM retrieves semantically similar past examples as few-shot context before generating new tests — the system gets smarter with every run.
          </p>
        </div>
      </div>

      {/* ── Run history table ── */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155' }}>
          <h3 style={{ fontSize: 15 }}>Run History</h3>
        </div>
        {recent_runs.length === 0 ? (
          <p style={{ padding: 32, textAlign: 'center', color: '#64748b' }}>
            No completed runs yet. <span style={{ color: '#60a5fa', cursor: 'pointer' }} onClick={() => nav('/runs/new')}>Start one →</span>
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Repository</th>
                <th>Mode</th>
                <th style={{ textAlign: 'center' }}>Functions</th>
                <th style={{ textAlign: 'center' }}>Pass Rate</th>
                <th style={{ textAlign: 'center' }}>Avg Coverage</th>
                <th style={{ textAlign: 'center' }}>Bugs Found</th>
                <th style={{ textAlign: 'center' }}>Fix</th>
                <th style={{ textAlign: 'right' }}>Duration</th>
              </tr>
            </thead>
            <tbody>
              {recent_runs.map(r => (
                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{RepoName(r.repo_url)}</div>
                    <div style={{ fontSize: 11, color: '#475569' }}>#{r.id}</div>
                  </td>
                  <td style={{ fontSize: 12, color: '#64748b' }}>
                    {r.function_name || 'whole-project'}
                  </td>
                  <td style={{ textAlign: 'center' }}>{r.function_count}</td>
                  <td style={{ textAlign: 'center' }}>
                    {r.pass_rate != null ? (
                      <span style={{ color: r.pass_rate >= 70 ? '#6ee7b7' : r.pass_rate >= 40 ? '#fde68a' : '#fca5a5', fontWeight: 600 }}>
                        {r.pass_rate}%
                      </span>
                    ) : <span style={{ color: '#475569' }}>—</span>}
                    {r.pass_rate != null && (
                      <div style={{ fontSize: 11, color: '#475569' }}>{r.total_passed}p / {r.total_failed}f</div>
                    )}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {r.avg_coverage_pct != null ? (
                      <span style={{ color: r.avg_coverage_pct >= 70 ? '#6ee7b7' : '#fde68a' }}>
                        {r.avg_coverage_pct}%
                      </span>
                    ) : <span style={{ color: '#475569' }}>—</span>}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {r.bugs_detected > 0
                      ? <span className="chip chip-fail">✗ {r.bugs_detected}</span>
                      : <span style={{ color: '#475569' }}>0</span>}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {r.has_fix ? <span className="chip chip-pass">✓</span> : <span style={{ color: '#475569' }}>—</span>}
                  </td>
                  <td style={{ textAlign: 'right', fontSize: 12, color: '#64748b' }}>
                    {elapsed(r.created_at, r.finished_at) || '—'}
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
