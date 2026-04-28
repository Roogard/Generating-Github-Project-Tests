import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRuns, deleteRun, createRun } from '../api.js'
import { isBenchmarkMode } from '../utils.js'

const SESSION_KEY = 'ggpt_session_run_ids'

function getSessionIds() {
  try { return new Set(JSON.parse(sessionStorage.getItem(SESSION_KEY) || '[]')) } catch { return new Set() }
}
function addSessionId(id) {
  const ids = getSessionIds()
  ids.add(id)
  sessionStorage.setItem(SESSION_KEY, JSON.stringify([...ids]))
}
function removeSessionId(id) {
  const ids = getSessionIds()
  ids.delete(id)
  sessionStorage.setItem(SESSION_KEY, JSON.stringify([...ids]))
}

const PROVIDERS = ['deepseek', 'openai', 'anthropic', 'ollama']
const PRESETS = ['fast', 'default', 'thorough']

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
  const nav = useNavigate()

  // ── runs list ──
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState('')

  const loadRuns = () => {
    const ids = getSessionIds()
    getRuns()
      .then(all => setRuns(all.filter(r => ids.has(r.id))))
      .catch(e => setListError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadRuns()
    const id = setInterval(loadRuns, 5000)
    return () => clearInterval(id)
  }, [])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this run and all its data?')) return
    await deleteRun(id)
    removeSessionId(id)
    setRuns(r => r.filter(x => x.id !== id))
  }

  // ── new run form ──
  const [form, setForm] = useState({
    repo_url: '',
    issue_text: '',
    api_key: '',
    provider: 'deepseek',
    model: '',
    preset: 'default',
    install_deps: true,
  })
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async e => {
    e.preventDefault()
    if (!form.repo_url.trim()) return setFormError('Repository URL is required')
    if (!form.issue_text.trim()) return setFormError('Issue text is required — the agent reads it to know what bug to test for')
    setFormError('')
    setSubmitting(true)
    try {
      const res = await createRun({
        source: 'repo',
        repo_url: form.repo_url.trim(),
        issue_text: form.issue_text.trim(),
        api_key: form.api_key.trim(),
        provider: form.provider,
        model: form.model.trim() || null,
        preset: form.preset,
        install_deps: form.install_deps,
      })
      addSessionId(res.id)
      nav(`/runs/${res.id}`)
    } catch (e) {
      setFormError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      {/* ── Runs list ── */}
      <div className="page-header">
        <h1 className="page-title">Runs</h1>
      </div>

      {listError && <div className="alert alert-error">{listError}</div>}
      {loading && <p style={{ color: 'var(--text-3)' }}>Loading...</p>}

      {!loading && runs.length === 0 && (
        <p style={{ color: 'var(--text-3)', marginBottom: 32 }}>No runs yet — start one below.</p>
      )}

      {runs.length > 0 && (
        <div className="card" style={{ padding: 0, marginBottom: 40, overflowX: 'auto' }}>
          <table style={{ minWidth: 760 }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Repository</th>
                <th>Mode</th>
                <th>Status</th>
                <th>Pass / Fail</th>
                <th>Outcome</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/runs/${r.id}`)}>
                  <td style={{ color: 'var(--text-3)', width: 50 }}>#{r.id}</td>
                  <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.repo_url}
                  </td>
                  <td style={{ color: 'var(--text-2)', fontSize: 12 }}>
                    {isBenchmarkMode(r.mode) && (
                      <span className="chip chip-bench" style={{ marginRight: 6 }}>BENCH</span>
                    )}
                    {r.mode}{r.benchmark_id ? `:${r.benchmark_id}` : ''}
                  </td>
                  <td>{statusBadge(r.status)}</td>
                  <td style={{ fontSize: 12 }}>
                    {(r.tests_passed + r.tests_failed) > 0
                      ? <><span style={{ color: 'var(--green-fg)' }}>{r.tests_passed}</span> / <span style={{ color: r.tests_failed > 0 ? 'var(--red-fg)' : 'var(--text-2)' }}>{r.tests_failed}</span></>
                      : <span style={{ color: 'var(--text-3)' }}>—</span>}
                  </td>
                  <td>
                    {r.resolved
                      ? <span className="chip chip-pass">S</span>
                      : <span style={{ color: 'var(--text-3)', fontSize: 12 }}>—</span>}
                    {r.f2p > 0 && <span style={{ fontSize: 11, color: 'var(--text-3)', marginLeft: 6 }}>F→P {r.f2p}</span>}
                  </td>
                  <td style={{ color: 'var(--text-3)', fontSize: 12 }}>{timeAgo(r.created_at)}</td>
                  <td onClick={e => e.stopPropagation()}>
                    <button className="btn-danger btn-sm" onClick={e => handleDelete(e, r.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── New run form ── */}
      <h2 style={{ fontSize: 16, marginBottom: 20, color: 'var(--text-2)' }}>New Run</h2>

      {formError && <div className="alert alert-error" style={{ marginBottom: 16 }}>{formError}</div>}

      <form onSubmit={submit}>
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>Repository &amp; Issue</h3>
          <div className="form-group">
            <label>GitHub Repository URL *</label>
            <input
              type="url"
              value={form.repo_url}
              onChange={e => set('repo_url', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Issue *</label>
            <textarea
              value={form.issue_text}
              onChange={e => set('issue_text', e.target.value)}
              placeholder="Paste the GitHub issue text — describe the bug, expected vs. actual behavior, reproducer steps. The agent reads this to know what to test for."
              rows={8}
              required
              style={{ fontFamily: 'inherit', resize: 'vertical', minHeight: 140 }}
            />
            <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4 }}>
              The agent localizes the relevant code itself by exploring the repo with read_file / search_in_repo tools. You don't need to point at a specific function.
            </div>
          </div>
          <div className="form-group">
            <label>API Key (passed to LLM provider)</label>
            <input
              type="password"
              value={form.api_key}
              onChange={e => set('api_key', e.target.value)}
            />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>LLM Settings</h3>
          <div className="grid-2">
            <div className="form-group">
              <label>Provider</label>
              <select value={form.provider} onChange={e => set('provider', e.target.value)}>
                {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Preset</label>
              <select value={form.preset} onChange={e => set('preset', e.target.value)}>
                {PRESETS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Model Override (optional)</label>
            <input
              type="text"
              value={form.model}
              onChange={e => set('model', e.target.value)}
            />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>Options</h3>
          <div className="toggle-row">
            <input type="checkbox" id="install_deps" checked={form.install_deps} onChange={e => set('install_deps', e.target.checked)} />
            <div>
              <div className="toggle-label">Install repo dependencies</div>
            </div>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={submitting} style={{ width: '100%', padding: '12px' }}>
          {submitting ? 'Starting...' : 'Start Test Generation'}
        </button>
      </form>
    </div>
  )
}
