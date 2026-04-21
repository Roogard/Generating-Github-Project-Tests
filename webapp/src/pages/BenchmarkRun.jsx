import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createBenchmark } from '../api.js'

const PROVIDERS = ['deepseek', 'openai', 'anthropic', 'ollama']
const PRESETS = ['fast', 'default', 'thorough']

export default function BenchmarkRun() {
  const nav = useNavigate()
  const [form, setForm] = useState({
    provider: 'deepseek',
    model: '',
    preset: 'default',
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
        <h1 className="page-title">QuixBugs Benchmark <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 8 }}>(admin)</span></h1>
        <button className="btn-ghost" onClick={() => nav('/')}>← Back</button>
      </div>

      <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 16 }}>
        Runs the QuixBugs oracle batch. Each program becomes its own Run, with
        SWT-bench transitions (F→P / F→F / P→F) recorded to the DB and surfaced
        on the Analytics page.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-info" style={{ marginBottom: 16 }}>{message}</div>}

      <form onSubmit={submit}>
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>QuixBugs</h3>
          <div className="form-group">
            <label>Phase</label>
            <select value={form.phase} onChange={e => set('phase', e.target.value)}>
              <option value="measure">Measure — evaluate on measure split</option>
              <option value="populate">Populate — ingest golden examples into ChromaDB</option>
            </select>
          </div>
          <div className="grid-2">
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
            <input type="checkbox" id="use_rag" checked={form.use_rag} onChange={e => set('use_rag', e.target.checked)} />
            <label htmlFor="use_rag" style={{ marginBottom: 0 }}>Use ChromaDB memory during generation (RAG retrieval)</label>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '12px' }}>
          {loading ? 'Starting…' : 'Start Benchmark'}
        </button>
      </form>
    </div>
  )
}
