import { useState } from 'react'
import { createRun } from '../api.js'

const PROVIDERS = ['deepseek', 'openai', 'anthropic', 'ollama']
const PRESETS = ['fast', 'default', 'thorough']
const DATASETS = [
  { value: 'swtbench_lite',     title: 'SWT-Bench Lite',     desc: '300 tasks — held-out measure split' },
  { value: 'swtbench_verified', title: 'SWT-Bench Verified', desc: '500 tasks — curated train split' },
]

export default function Benchmark() {
  const [form, setForm] = useState({
    provider: 'deepseek',
    model: '',
    preset: 'default',
    api_key: '',
    dataset: 'swtbench_lite',
    instance_limit: 10,
    instance_ids: '',
    use_official_images: true,
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
      const ids = form.instance_ids.trim()
      await createRun({
        source: 'swtbench',
        provider: form.provider,
        model: form.model.trim() || null,
        preset: form.preset,
        api_key: form.api_key.trim(),
        dataset: form.dataset,
        instance_limit: form.instance_limit ? parseInt(form.instance_limit) : null,
        instance_ids: ids ? ids.split(/[\s,]+/).filter(Boolean) : null,
        use_official_images: form.use_official_images,
      })
      setMessage(
        'SWT-Bench run started in the background. Each instance becomes its own Run — ' +
        'visit the Runs list to watch progress. Results feed into Analytics automatically.'
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
          <h1 className="page-title">SWT-Bench</h1>
          <p className="page-sub">Real-world bug reproduction tasks from SWE-Bench. Each instance = one GitHub issue + buggy repo snapshot + gold fix patch. F→P / F→F / P→F transitions are recorded after each run.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-info">{message}</div>}

      <form onSubmit={submit}>
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-label" style={{ marginBottom: 14 }}>Dataset</div>
          <div className="grid-2" style={{ gap: 12 }}>
            {DATASETS.map(d => (
              <div
                key={d.value}
                onClick={() => set('dataset', d.value)}
                style={{
                  border: `1px solid ${form.dataset === d.value ? 'var(--blue)' : 'var(--border)'}`,
                  background: form.dataset === d.value ? 'rgba(59,130,246,0.06)' : 'var(--surface)',
                  borderRadius: 8, padding: '14px 16px', cursor: 'pointer',
                  transition: 'border-color 0.12s, background 0.12s',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, color: form.dataset === d.value ? 'var(--blue)' : 'var(--text)' }}>
                  {d.title}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{d.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-label" style={{ marginBottom: 14 }}>Instances</div>
          <div className="grid-2">
            <div className="form-group">
              <label>Instance limit</label>
              <input
                type="number" min="1"
                value={form.instance_limit}
                onChange={e => set('instance_limit', e.target.value)}
                placeholder="blank = all"
              />
            </div>
            <div className="form-group">
              <label>Instance IDs (optional)</label>
              <input
                type="text"
                value={form.instance_ids}
                onChange={e => set('instance_ids', e.target.value)}
                placeholder="comma/space-separated"
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
            <input type="checkbox" id="use_official_images" checked={form.use_official_images} onChange={e => set('use_official_images', e.target.checked)} />
            <div>
              <div className="toggle-label">Use official SWT-Bench images</div>
              <div className="toggle-hint">
                Pulls <code>swebench/sweb.eval.x86_64.&lt;instance&gt;:latest</code> per instance
                (~1&nbsp;GB each, era-correct Python+deps pre-installed). Required for the long
                tail of repos that don't build against Python&nbsp;3.12. Off ⇒ uses generic
                <code>ggpt-runtime</code> image; many instances will fail env_setup.
              </div>
            </div>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '12px' }}>
          {loading ? 'Starting…' : 'Start SWT-Bench Run'}
        </button>
      </form>
    </div>
  )
}
