import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRun, getRunStatus, downloadRun, promoteRunToMemory } from '../api.js'
import { useAdmin, isBenchmarkMode } from '../admin.js'

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

function BenchmarkPanel({ run }) {
  if (!isBenchmarkMode(run.mode)) return null
  const dot = (label, value, tone) => (
    <div className="stat-card" style={{ minWidth: 90 }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 18, color: tone }}>{value}</div>
    </div>
  )
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 14, marginBottom: 10 }}>
        SWT-bench Oracle  ·  <span style={{ color: '#64748b' }}>{run.mode}:{run.benchmark_id}</span>
      </h3>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {dot('F→P', run.f2p, run.f2p > 0 ? '#6ee7b7' : '#94a3b8')}
        {dot('F→F', run.f2f, run.f2f > 0 ? '#fca5a5' : '#94a3b8')}
        {dot('P→F', run.p2f, run.p2f > 0 ? '#fca5a5' : '#94a3b8')}
        {dot('P→P', run.p2p ?? '—', '#94a3b8')}
        {dot('Resolved', run.resolved ? 'YES' : 'no', run.resolved ? '#6ee7b7' : '#94a3b8')}
      </div>
    </div>
  )
}

function AdminCurationBlock({ run, onPromote, promoting, promoteMsg }) {
  return (
    <div
      className="card"
      style={{ marginBottom: 20, borderColor: '#22c55e', background: '#0f1f38' }}
    >
      <h3 style={{ fontSize: 14, marginBottom: 10, color: '#bbf7d0' }}>
        Admin curation
      </h3>
      {promoteMsg && <div className="alert alert-info" style={{ marginBottom: 10 }}>{promoteMsg}</div>}

      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        {run.promoted_to_memory_at ? (
          <span className="badge badge-done" title={run.promoted_to_memory_at}>
            ✓ Promoted to memory
          </span>
        ) : (
          <button className="btn-ghost btn-sm" onClick={onPromote} disabled={promoting}>
            {promoting ? 'Promoting…' : '📥 Promote to vector DB'}
          </button>
        )}
        <span style={{ fontSize: 12, color: '#64748b' }}>
          Promote copies each qualifying function's whitebox + blackbox tests into
          ChromaDB for RAG retrieval on future runs.
        </span>
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
          <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{fn.name}</span>
          <span style={{ fontSize: 12, color: '#64748b' }}>{fn.file_path}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {fn.tests_passed > 0 && <span className="chip chip-pass">✓ {fn.tests_passed}</span>}
          {fn.tests_failed > 0 && <span className="chip chip-fail">✗ {fn.tests_failed}</span>}
          <span style={{ color: '#64748b', fontSize: 18 }}>{open ? '▲' : '▼'}</span>
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
              <div className="stat-value" style={{ fontSize: 18, color: '#6ee7b7' }}>{fn.tests_passed}</div>
            </div>
            <div className="stat-card" style={{ minWidth: 100 }}>
              <div className="stat-label">Failed</div>
              <div className="stat-value" style={{ fontSize: 18, color: fn.tests_failed > 0 ? '#fca5a5' : '#6ee7b7' }}>{fn.tests_failed}</div>
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
  const [promoting, setPromoting] = useState(false)
  const [promoteMsg, setPromoteMsg] = useState('')
  const admin = useAdmin()

  const loadFull = () => getRun(id).then(setRun).catch(e => setError(e.message))

  const onPromote = async () => {
    setPromoting(true)
    setPromoteMsg('')
    try {
      const r = await promoteRunToMemory(run.id)
      const skipSummary = Object.entries(r.skipped || {})
        .map(([k, v]) => `${k}: ${v}`).join(', ')
      setPromoteMsg(
        `Ingested ${r.ingested} example${r.ingested === 1 ? '' : 's'}` +
        (skipSummary ? ` (skipped — ${skipSummary})` : '')
      )
      loadFull()
    } catch (e) {
      setPromoteMsg(e.message)
    } finally {
      setPromoting(false)
    }
  }

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
    <div className="page"><p style={{ color: '#64748b' }}>Loading...</p></div>
  )

  const showAdminBlock = admin && run.status === 'done'

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button className="btn-ghost btn-sm" style={{ marginBottom: 8 }} onClick={() => nav('/')}>← Runs</button>
          <h1 className="page-title" style={{ fontSize: 18 }}>{run.repo_url}</h1>
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
            <div className="stat-value" style={{ color: '#6ee7b7' }}>{run.tests_passed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tests Failed</div>
            <div className="stat-value" style={{ color: run.tests_failed > 0 ? '#fca5a5' : '#6ee7b7' }}>{run.tests_failed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg Coverage</div>
            <div className="stat-value">{run.avg_coverage_pct != null ? `${Math.round(run.avg_coverage_pct)}%` : '—'}</div>
          </div>
        </div>
      )}

      <BenchmarkPanel run={run} />

      {showAdminBlock && (
        <AdminCurationBlock
          run={run}
          onPromote={onPromote}
          promoting={promoting}
          promoteMsg={promoteMsg}
        />
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
