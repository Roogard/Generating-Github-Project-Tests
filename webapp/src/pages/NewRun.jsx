import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRun } from '../api.js'

const PROVIDERS = ['deepseek', 'openai', 'anthropic', 'ollama']
const PRESETS = ['fast', 'default', 'thorough']

export default function NewRun() {
  const nav = useNavigate()
  const [form, setForm] = useState({
    repo_url: '',
    api_key: '',
    provider: 'deepseek',
    model: '',
    preset: 'default',
    function_limit: '',
    fix_pass: false,
    install_deps: true,
    save_to_db: false,
    save_to_rag: false,
    rag_success_only: true,
    use_rag: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async e => {
    e.preventDefault()
    if (!form.repo_url.trim()) return setError('Repository URL is required')
    setError('')
    setLoading(true)
    try {
      const body = {
        repo_url: form.repo_url.trim(),
        api_key: form.api_key.trim(),
        provider: form.provider,
        model: form.model.trim() || null,
        preset: form.preset,
        fix_pass: form.fix_pass,
        install_deps: form.install_deps,
        save_to_db: form.save_to_db,
        save_to_rag: form.save_to_rag,
        rag_success_only: form.rag_success_only,
        use_rag: form.use_rag,
        function_limit: form.function_limit ? parseInt(form.function_limit) : null,
      }
      const res = await createRun(body)
      nav(`/runs/${res.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page" style={{ maxWidth: 680 }}>
      <div className="page-header">
        <h1 className="page-title">New Test Generation Run</h1>
        <button className="btn-ghost" onClick={() => nav('/')}>← Back</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={submit}>
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>Repository</h3>
          <div className="form-group">
            <label>GitHub Repository URL *</label>
            <input
              type="url"
              placeholder="https://github.com/owner/repo"
              value={form.repo_url}
              onChange={e => set('repo_url', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>API Key (passed to LLM provider)</label>
            <input
              type="password"
              placeholder="sk-... or leave blank to use server .env"
              value={form.api_key}
              onChange={e => set('api_key', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Function Limit (leave blank for all functions)</label>
            <input
              type="number"
              placeholder="e.g. 10"
              min="1"
              value={form.function_limit}
              onChange={e => set('function_limit', e.target.value)}
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
              placeholder="e.g. deepseek-chat"
              value={form.model}
              onChange={e => set('model', e.target.value)}
            />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>Options</h3>
          <div className="toggle-row">
            <input type="checkbox" id="fix_pass" checked={form.fix_pass} onChange={e => set('fix_pass', e.target.checked)} />
            <label htmlFor="fix_pass" style={{ marginBottom: 0 }}>
              Fix Pass — generate proposed code fix when tests fail
            </label>
          </div>
          <div className="toggle-row">
            <input type="checkbox" id="install_deps" checked={form.install_deps} onChange={e => set('install_deps', e.target.checked)} />
            <label htmlFor="install_deps" style={{ marginBottom: 0 }}>Install repo dependencies</label>
          </div>
          <div className="toggle-row">
            <input type="checkbox" id="save_to_db" checked={form.save_to_db} onChange={e => set('save_to_db', e.target.checked)} />
            <label htmlFor="save_to_db" style={{ marginBottom: 0 }}>Save full results to SQLite database</label>
          </div>
          <div className="toggle-row">
            <input type="checkbox" id="use_rag" checked={form.use_rag} onChange={e => set('use_rag', e.target.checked)} />
            <label htmlFor="use_rag" style={{ marginBottom: 0 }}>
              Use ChromaDB memory during generation (RAG retrieval)
            </label>
          </div>
          <div className="toggle-row">
            <input type="checkbox" id="save_to_rag" checked={form.save_to_rag} onChange={e => set('save_to_rag', e.target.checked)} />
            <label htmlFor="save_to_rag" style={{ marginBottom: 0 }}>Save tests to ChromaDB (RAG memory)</label>
          </div>
          <div className="toggle-row">
            <input type="checkbox" id="rag_only" checked={form.rag_success_only} onChange={e => set('rag_success_only', e.target.checked)} />
            <label htmlFor="rag_only" style={{ marginBottom: 0 }}>Only store in ChromaDB if at least one test passed</label>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '12px' }}>
          {loading ? 'Starting...' : 'Start Test Generation'}
        </button>
      </form>
    </div>
  )
}
