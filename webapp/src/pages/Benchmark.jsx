import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createBenchmark } from '../api.js'

const PROVIDERS = ['deepseek', 'openai', 'anthropic', 'ollama']
const PRESETS = ['fast', 'default', 'thorough']

export default function Benchmark() {
  const nav = useNavigate()
  const [form, setForm] = useState({
    provider: 'deepseek',
    model: '',
    preset: 'default',
    api_key: '',
    use_rag: true,
    phase: 'measure',
    seed: 42,
    populate_count: 30,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async e => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)
    try {
      await createBenchmark({
        provider: form.provider,
        model: form.model.trim() || null,
        preset: form.preset,
        api_key: form.api_key.trim(),
        use_rag: form.use_rag,
        phase: form.phase,
        seed: parseInt(form.seed) || 42,
        populate_count: parseInt(form.populate_count) || 30,
      })
      setMessage(
        'Benchmark started in the background. Each QuixBugs program becomes its own ' +
        'Run — visit the Runs list to watch progress. Results feed into Analytics ' +
        'automatically.'
      )
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page" style={{ maxWidth: 680 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">QuixBugs Benchmark</h1>
          <p className="page-sub">Runs the QuixBugs oracle batch — each program becomes its own Run with SWT-bench transitions recorded.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-info">{message}</div>}

      <form onSubmit={submit}>
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-label" style={{ marginBottom: 14 }}>Phase</div>
          <div className="grid-2" style={{ gap: 12 }}>
            {[
              { value: 'measure', title: 'Measure', desc: 'Evaluate on the measure split' },
              { value: 'populate', title: 'Populate', desc: 'Ingest golden examples into ChromaDB' },
            ].map(p => (
              <div
                key={p.value}
                onClick={() => set('phase', p.value)}
                style={{
                  border: `1px solid ${form.phase === p.value ? 'var(--blue)' : 'var(--border)'}`,
                  background: form.phase === p.value ? 'rgba(59,130,246,0.06)' : 'var(--surface)',
                  borderRadius: 8, padding: '14px 16px', cursor: 'pointer',
                  transition: 'border-color 0.12s, background 0.12s',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, color: form.phase === p.value ? 'var(--blue)' : 'var(--text)' }}>
                  {p.title}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{p.desc}</div>
              </div>
            ))}
          </div>
          <div className="grid-2" style={{ marginTop: 16 }}>
            <div className="form-group">
              <label>Populate count</label>
              <input
                type="number" min="1" max="40"
                value={form.populate_count}
                onChange={e => set('populate_count', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Split seed</label>
              <input
                type="number"
                value={form.seed}
                onChange={e => set('seed', e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-label" style={{ marginBottom: 14 }}>LLM Settings</div>
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
          <div className="form-group">
            <label>API Key</label>
            <input
              type="password"
              value={form.api_key}
              onChange={e => set('api_key', e.target.value)}
            />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <div className="toggle-row">
            <input type="checkbox" id="use_rag" checked={form.use_rag} onChange={e => set('use_rag', e.target.checked)} />
            <div>
              <div className="toggle-label">Use RAG memory</div>
              <div className="toggle-hint">Retrieve similar examples from ChromaDB during generation</div>
            </div>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '12px' }}>
          {loading ? 'Starting…' : 'Start Benchmark'}
        </button>
      </form>
    </div>
  )
}
