import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRun, getRunStatus, downloadRun } from '../api.js'

function Badge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

function ProgressSection({ current, total, status }) {
  if (status !== 'running' || total === 0) return null
  const pct = Math.round((current / total) * 100)
  return (
    <div className="alert alert-info" style={{ marginBottom: 20 }}>
      <strong>Running...</strong> {current}/{total} functions complete ({pct}%)
      <div className="progress-bar-wrap" style={{ marginTop: 8 }}>
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function FunctionCard({ fn }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState('whitebox')

  const totalPassed = fn.tests.reduce((s, t) => s + t.passed, 0)
  const totalFailed = fn.tests.reduce((s, t) => s + t.failed, 0)

  return (
    <div className="card" style={{ padding: 0, marginBottom: 12 }}>
      <div className="accordion-header" onClick={() => setOpen(o => !o)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{fn.name}</span>
          <span style={{ fontSize: 12, color: '#64748b' }}>{fn.file_path}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {totalPassed > 0 && <span className="chip chip-pass">✓ {totalPassed}</span>}
          {totalFailed > 0 && <span className="chip chip-fail">✗ {totalFailed}</span>}
          <span style={{ color: '#64748b', fontSize: 18 }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {open && (
        <div className="accordion-body">
          {/* Coverage row */}
          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            {fn.tests.map(t => (
              <div key={t.id} className="stat-card" style={{ minWidth: 100 }}>
                <div className="stat-label">{t.type}</div>
                <div className="stat-value" style={{ fontSize: 18 }}>
                  {t.coverage_pct != null ? `${Math.round(t.coverage_pct)}%` : '—'}
                </div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                  {t.passed}p {t.failed}f
                </div>
              </div>
            ))}
          </div>

          {/* Test code tabs */}
          {fn.tests.length > 0 && (
            <>
              <div className="tabs">
                {fn.tests.map(t => (
                  <div key={t.type} className={`tab${tab === t.type ? ' active' : ''}`} onClick={() => setTab(t.type)}>
                    {t.type}
                  </div>
                ))}
                {fn.fixes.length > 0 && (
                  <div className={`tab${tab === 'fix' ? ' active' : ''}`} onClick={() => setTab('fix')}>
                    proposed fix
                  </div>
                )}
                {fn.failures.length > 0 && (
                  <div className={`tab${tab === 'failures' ? ' active' : ''}`} onClick={() => setTab('failures')}>
                    failures ({fn.failures.length})
                  </div>
                )}
              </div>

              {tab === 'fix' && fn.fixes[0] && (
                <div>
                  {fn.fixes[0].diagnosis && (
                    <p style={{ color: '#94a3b8', marginBottom: 12, fontSize: 13 }}>{fn.fixes[0].diagnosis}</p>
                  )}
                  <pre className="code-block">{fn.fixes[0].fixed_code || '— no code generated —'}</pre>
                </div>
              )}

              {tab === 'failures' && (
                <div>
                  {fn.failures.map((f, i) => (
                    <div key={i} style={{ marginBottom: 16 }}>
                      <div style={{ fontFamily: 'monospace', color: '#fca5a5', marginBottom: 4, fontSize: 13 }}>
                        [{f.kind.toUpperCase()}] {f.test_name}
                      </div>
                      {f.assertion && <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>{f.assertion}</div>}
                      {f.longrepr && <pre className="code-block" style={{ fontSize: 12 }}>{f.longrepr.slice(0, 800)}</pre>}
                    </div>
                  ))}
                </div>
              )}

              {['whitebox', 'blackbox'].includes(tab) && (() => {
                const t = fn.tests.find(x => x.type === tab)
                return t ? <pre className="code-block">{t.code || '— no code —'}</pre> : null
              })()}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default function RunDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const [run, setRun] = useState(null)
  const [error, setError] = useState('')

  const loadFull = () => getRun(id).then(setRun).catch(e => setError(e.message))

  useEffect(() => {
    loadFull()
  }, [id])

  // Poll status while running
  useEffect(() => {
    if (!run || run.status !== 'running') return
    const timer = setInterval(() => {
      getRunStatus(id)
        .then(s => {
          setRun(r => r ? { ...r, status: s.status, progress_current: s.progress_current, progress_total: s.progress_total, error_message: s.error_message } : r)
          if (s.status !== 'running') {
            clearInterval(timer)
            loadFull()
          }
        })
        .catch(() => {})
    }, 3000)
    return () => clearInterval(timer)
  }, [run?.status])

  if (error) return (
    <div className="page"><div className="alert alert-error">{error}</div></div>
  )
  if (!run) return (
    <div className="page"><p style={{ color: '#64748b' }}>Loading...</p></div>
  )

  const totalPassed = run.functions.reduce((s, fn) => s + fn.tests.reduce((ss, t) => ss + t.passed, 0), 0)
  const totalFailed = run.functions.reduce((s, fn) => s + fn.tests.reduce((ss, t) => ss + t.failed, 0), 0)

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button className="btn-ghost btn-sm" style={{ marginBottom: 8 }} onClick={() => nav('/')}>← Runs</button>
          <h1 className="page-title" style={{ fontSize: 18 }}>{run.repo_url}</h1>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {run.status === 'done' && run.output_dir && (
            <button className="btn-primary" onClick={() => downloadRun(run.id)}>⬇ Download ZIP</button>
          )}
          <span><Badge status={run.status} /></span>
        </div>
      </div>

      <ProgressSection current={run.progress_current} total={run.progress_total} status={run.status} />

      {run.error_message && <div className="alert alert-error">{run.error_message}</div>}

      {run.status === 'done' && (
        <div className="stat-row">
          <div className="stat-card">
            <div className="stat-label">Functions</div>
            <div className="stat-value">{run.functions.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tests Passed</div>
            <div className="stat-value" style={{ color: '#6ee7b7' }}>{totalPassed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tests Failed</div>
            <div className="stat-value" style={{ color: totalFailed > 0 ? '#fca5a5' : '#6ee7b7' }}>{totalFailed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Fix Passes</div>
            <div className="stat-value">{run.functions.filter(f => f.fixes.length > 0).length}</div>
          </div>
        </div>
      )}

      {run.functions.length > 0 && (
        <>
          <h2 style={{ fontSize: 16, marginBottom: 12, color: '#94a3b8' }}>Functions</h2>
          {run.functions.map(fn => <FunctionCard key={fn.id} fn={fn} />)}
        </>
      )}

      {run.status === 'running' && run.functions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          Pipeline is running. Results will appear here as functions complete.
        </div>
      )}
    </div>
  )
}
