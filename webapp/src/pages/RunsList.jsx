import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRuns, deleteRun } from '../api.js'
import { isBenchmarkMode } from '../admin.js'

function statusBadge(status) {
  return <span className={`badge badge-${status}`}>{status}</span>
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

export default function RunsList() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const nav = useNavigate()

  const load = () => {
    getRuns()
      .then(setRuns)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this run and all its data?')) return
    await deleteRun(id)
    setRuns(r => r.filter(x => x.id !== id))
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Test Generation Runs</h1>
        <button className="btn-primary" onClick={() => nav('/runs/new')}>+ New Run</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p style={{ color: '#64748b' }}>Loading...</p>}

      {!loading && runs.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          <p style={{ marginBottom: 16 }}>No runs yet.</p>
          <button className="btn-primary" onClick={() => nav('/runs/new')}>Start your first run</button>
        </div>
      )}

      {runs.length > 0 && (
        <div className="card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Repository</th>
                <th>Mode</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Functions</th>
                <th>Pass / Fail</th>
                <th>Outcome</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                  <td style={{ color: '#64748b', width: 50 }}>#{r.id}</td>
                  <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.repo_url}
                  </td>
                  <td style={{ color: '#94a3b8', fontSize: 12 }}>
                    {isBenchmarkMode(r.mode) && (
                      <span
                        className="chip"
                        style={{
                          marginRight: 6,
                          background: '#1e293b',
                          color: '#fbbf24',
                          borderColor: '#b45309',
                          fontSize: 10,
                        }}
                      >
                        BENCH
                      </span>
                    )}
                    {r.mode}{r.benchmark_id ? `:${r.benchmark_id}` : ''}
                  </td>
                  <td>{statusBadge(r.status)}</td>
                  <td style={{ width: 140 }}>
                    {r.status === 'running' && r.progress_total > 0 ? (
                      <div>
                        <div className="progress-bar-wrap">
                          <div className="progress-bar-fill" style={{ width: `${(r.progress_current / r.progress_total) * 100}%` }} />
                        </div>
                        <span style={{ fontSize: 11, color: '#64748b' }}>{r.progress_current}/{r.progress_total}</span>
                      </div>
                    ) : '—'}
                  </td>
                  <td>{r.function_count ?? '—'}</td>
                  <td style={{ fontSize: 12 }}>
                    {(r.tests_passed + r.tests_failed) > 0
                      ? <><span style={{ color: '#6ee7b7' }}>{r.tests_passed}</span> / <span style={{ color: r.tests_failed > 0 ? '#fca5a5' : '#94a3b8' }}>{r.tests_failed}</span></>
                      : <span style={{ color: '#475569' }}>—</span>}
                  </td>
                  <td>
                    {r.resolved
                      ? <span className="chip chip-pass">S</span>
                      : <span style={{ color: '#475569', fontSize: 12 }}>—</span>}
                    {r.f2p > 0 && <span style={{ fontSize: 11, color: '#64748b', marginLeft: 6 }}>F→P {r.f2p}</span>}
                  </td>
                  <td style={{ color: '#64748b', fontSize: 12 }}>{timeAgo(r.created_at)}</td>
                  <td onClick={e => e.stopPropagation()}>
                    <button className="btn-danger btn-sm" onClick={e => handleDelete(e, r.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
