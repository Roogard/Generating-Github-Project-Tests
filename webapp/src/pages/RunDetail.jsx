import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRun, getRunStatus, downloadRun } from '../api.js'
import { isBenchmarkMode } from '../utils.js'

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

function OracleMatrix({ run }) {
  const cells = [
    { code: 'F→P', value: run.f2p, hint: 'fail→pass', cls: 'good' },
    { code: 'F→F', value: run.f2f, hint: 'fail→fail', cls: 'bad' },
    { code: 'P→F', value: run.p2f, hint: 'pass→fail', cls: 'bad' },
    { code: 'P→P', value: run.p2p ?? 0, hint: 'pass→pass', cls: '' },
  ]
  return (
    <div className="card" style={{ padding: 0, marginBottom: 20 }}>
      <div className="card-header">
        <h3>SWT-bench Oracle · <span style={{ color: 'var(--text-3)', fontWeight: 400 }}>{run.mode}:{run.benchmark_id}</span></h3>
        {run.resolved
          ? <span className="chip chip-pass">S Resolved</span>
          : <span style={{ fontSize: 12, color: 'var(--text-3)' }}>Not resolved</span>}
      </div>
      <div className="oracle-grid">
        <div className="oracle-corner">
          buggy<span className="arrow">→</span>golden
        </div>
        <div className="oracle-col-head">Pass</div>
        <div className="oracle-col-head">Fail</div>
        <div className="oracle-row-head">Fail</div>
        <div className={`oracle-cell ${cells[0].cls}`}>
          <div className="oracle-cell-code">{cells[0].code}</div>
          <div className="oracle-cell-value" style={{ color: cells[0].value > 0 ? 'var(--green-fg)' : 'var(--text)' }}>{cells[0].value}</div>
          <div className="oracle-cell-hint">{cells[0].hint}</div>
        </div>
        <div className={`oracle-cell ${cells[1].cls} no-right-border`}>
          <div className="oracle-cell-code">{cells[1].code}</div>
          <div className="oracle-cell-value" style={{ color: cells[1].value > 0 ? 'var(--red-fg)' : 'var(--text)' }}>{cells[1].value}</div>
          <div className="oracle-cell-hint">{cells[1].hint}</div>
        </div>
        <div className="oracle-row-head">Pass</div>
        <div className={`oracle-cell ${cells[2].cls} last-row`}>
          <div className="oracle-cell-code">{cells[2].code}</div>
          <div className="oracle-cell-value" style={{ color: cells[2].value > 0 ? 'var(--red-fg)' : 'var(--text)' }}>{cells[2].value}</div>
          <div className="oracle-cell-hint">{cells[2].hint}</div>
        </div>
        <div className={`oracle-cell last-row no-right-border`}>
          <div className="oracle-cell-code">{cells[3].code}</div>
          <div className="oracle-cell-value">{cells[3].value}</div>
          <div className="oracle-cell-hint">{cells[3].hint}</div>
        </div>
      </div>
      <div className="matrix-legend">
        <div className="matrix-legend-item">
          <div className="dot" style={{ background: 'var(--green-fg)' }} />
          F→P: tests that detect the bug (true positives)
        </div>
        <div className="matrix-legend-item">
          <div className="dot" style={{ background: 'var(--red-fg)' }} />
          F→F / P→F: spurious failures or regressions
        </div>
      </div>
    </div>
  )
}

function FunctionCard({ fn }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState('whitebox')

  return (
    <div className="card" style={{ padding: 0, marginBottom: 12 }}>
      <div className="accordion-header" onClick={() => setOpen(o => !o)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontFamily: 'var(--mono)', fontWeight: 600 }}>{fn.name}</span>
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{fn.file_path}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {fn.tests_passed > 0 && <span className="chip chip-pass">✓ {fn.tests_passed}</span>}
          {fn.tests_failed > 0 && <span className="chip chip-fail">✗ {fn.tests_failed}</span>}
          <span style={{ color: 'var(--text-3)', fontSize: 18 }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {open && (
        <div className="accordion-body">
          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <div className="stat-card" style={{ minWidth: 100 }}>
              <div className="stat-label">Coverage</div>
              <div className="stat-value" style={{ fontSize: 18 }}>
                {fn.coverage_pct != null ? `${Math.round(fn.coverage_pct)}%` : '—'}
              </div>
            </div>
            <div className="stat-card" style={{ minWidth: 100 }}>
              <div className="stat-label">Passed</div>
              <div className="stat-value" style={{ fontSize: 18, color: 'var(--green-fg)' }}>{fn.tests_passed}</div>
            </div>
            <div className="stat-card" style={{ minWidth: 100 }}>
              <div className="stat-label">Failed</div>
              <div className="stat-value" style={{ fontSize: 18, color: fn.tests_failed > 0 ? 'var(--red-fg)' : 'var(--green-fg)' }}>{fn.tests_failed}</div>
            </div>
          </div>

          <div className="tabs">
            <div className={`tab${tab === 'whitebox' ? ' active' : ''}`} onClick={() => setTab('whitebox')}>whitebox</div>
            <div className={`tab${tab === 'blackbox' ? ' active' : ''}`} onClick={() => setTab('blackbox')}>blackbox</div>
          </div>

          <pre className="code-block">
            {(tab === 'whitebox' ? fn.whitebox_code : fn.blackbox_code) || '— no code —'}
          </pre>
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
    <div className="page"><p style={{ color: 'var(--text-3)' }}>Loading...</p></div>
  )

  const isBench = isBenchmarkMode(run.mode)

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button className="btn-ghost btn-sm" style={{ marginBottom: 8 }} onClick={() => nav(-1)}>← Back</button>
          <h1 className="page-title" style={{ fontSize: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
            {run.repo_url}
            {isBench && <span className="chip chip-bench">BENCH</span>}
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
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
            <div className="stat-value" style={{ color: 'var(--green-fg)' }}>{run.tests_passed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tests Failed</div>
            <div className="stat-value" style={{ color: run.tests_failed > 0 ? 'var(--red-fg)' : 'var(--green-fg)' }}>{run.tests_failed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg Coverage</div>
            <div className="stat-value">{run.avg_coverage_pct != null ? `${Math.round(run.avg_coverage_pct)}%` : '—'}</div>
          </div>
        </div>
      )}

      {isBench && <OracleMatrix run={run} />}

      {run.functions.length > 0 && (
        <>
          <h2 style={{ fontSize: 16, marginBottom: 12, color: 'var(--text-2)' }}>Functions</h2>
          {run.functions.map(fn => <FunctionCard key={fn.id} fn={fn} />)}
        </>
      )}

      {run.status === 'running' && run.functions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-3)' }}>
          Pipeline is running. Results will appear here as functions complete.
        </div>
      )}
    </div>
  )
}
