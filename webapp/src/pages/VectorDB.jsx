import { useEffect, useState } from 'react'
import { getVectorStats, vectorSearch, getVectorExamples } from '../api.js'

function ExampleCard({ ex }) {
  const [showCode, setShowCode] = useState(false)
  const [showSource, setShowSource] = useState(false)

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div>
          <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{ex.fn_name}</span>
          <span style={{ marginLeft: 8, fontSize: 12, color: '#64748b' }}>{ex.fn_file}</span>
          <span style={{ marginLeft: 8 }} className={`badge badge-${ex.test_type === 'whitebox' ? 'running' : 'pending'}`}>{ex.test_type}</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {ex.coverage_pct != null && <span style={{ fontSize: 12, color: '#6ee7b7' }}>{Math.round(ex.coverage_pct)}% cov</span>}
          <span className="chip chip-pass">✓ {ex.passed}</span>
          {ex.failed > 0 && <span className="chip chip-fail">✗ {ex.failed}</span>}
        </div>
      </div>

      {ex.repo_url && <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>{ex.repo_url}</div>}

      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn-ghost btn-sm" onClick={() => setShowSource(s => !s)}>
          {showSource ? 'Hide' : 'Show'} Source
        </button>
        <button className="btn-ghost btn-sm" onClick={() => setShowCode(s => !s)}>
          {showCode ? 'Hide' : 'Show'} Test Code
        </button>
      </div>

      {showSource && ex.fn_source && (
        <pre className="code-block" style={{ marginTop: 10 }}>{ex.fn_source}</pre>
      )}
      {showCode && ex.test_code && (
        <pre className="code-block" style={{ marginTop: 10 }}>{ex.test_code}</pre>
      )}
    </div>
  )
}

export default function VectorDB() {
  const [stats, setStats] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState('whitebox')
  const [searchN, setSearchN] = useState(3)
  const [searchResults, setSearchResults] = useState(null)
  const [examples, setExamples] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filterType, setFilterType] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const LIMIT = 20

  useEffect(() => {
    getVectorStats().then(setStats).catch(() => {})
  }, [])

  const loadExamples = () => {
    getVectorExamples(page, LIMIT, filterType)
      .then(r => { setExamples(r.examples); setTotal(r.total) })
      .catch(e => setError(e.message))
  }

  useEffect(() => { setPage(1) }, [filterType])
  useEffect(() => { loadExamples() }, [page, filterType])

  const doSearch = async () => {
    if (!searchQuery.trim()) return
    setLoading(true)
    setSearchResults(null)
    try {
      const r = await vectorSearch(searchQuery.trim(), searchType, searchN)
      setSearchResults(r.results)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Vector Database</h1>
        <span style={{ color: '#64748b', fontSize: 13 }}>ChromaDB — RAG Memory</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {stats && (
        <div className="stat-row" style={{ marginBottom: 24 }}>
          <div className="stat-card">
            <div className="stat-label">Stored Examples</div>
            <div className="stat-value">{stats.count}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Collection</div>
            <div className="stat-value" style={{ fontSize: 16 }}>{stats.collection_name}</div>
          </div>
        </div>
      )}

      {/* Similarity Search */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 15, marginBottom: 14 }}>Similarity Search</h3>
        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 14 }}>
          Paste a Python function's source code to find similar past examples from the RAG store.
        </p>
        <div className="form-group">
          <label>Function Source Code</label>
          <textarea
            rows={6}
            placeholder="def my_function(x, y):\n    ..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <label>Test Type</label>
            <select value={searchType} onChange={e => setSearchType(e.target.value)}>
              <option value="whitebox">whitebox</option>
              <option value="blackbox">blackbox</option>
            </select>
          </div>
          <div style={{ width: 120 }}>
            <label>Results (n)</label>
            <input type="number" min="1" max="20" value={searchN} onChange={e => setSearchN(parseInt(e.target.value))} />
          </div>
          <button className="btn-primary" onClick={doSearch} disabled={loading} style={{ marginBottom: 0, whiteSpace: 'nowrap' }}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {searchResults && (
          <div>
            <h4 style={{ fontSize: 14, marginBottom: 10, color: '#94a3b8' }}>
              {searchResults.length} result(s) found
            </h4>
            {searchResults.length === 0 && (
              <p style={{ color: '#64748b' }}>No similar examples found. Run some test generations first to populate the store.</p>
            )}
            {searchResults.map((ex, i) => (
              <ExampleCard key={i} ex={ex} />
            ))}
          </div>
        )}
      </div>

      {/* Stored Examples Browser */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 16 }}>Stored Examples ({total})</h2>
          <select style={{ width: 160 }} value={filterType} onChange={e => setFilterType(e.target.value)}>
            <option value="">All types</option>
            <option value="whitebox">whitebox</option>
            <option value="blackbox">blackbox</option>
          </select>
        </div>

        {total === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
            <p>No examples stored yet.</p>
            <p style={{ marginTop: 8, fontSize: 13 }}>Run test generation with "Save to ChromaDB" enabled to populate the vector store.</p>
          </div>
        ) : (
          <>
            {examples.map((ex, i) => <ExampleCard key={i} ex={ex} />)}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', fontSize: 13, color: '#64748b', marginTop: 12 }}>
              <button className="btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
              <span>Page {page}</span>
              <button className="btn-ghost btn-sm" disabled={page * LIMIT >= total} onClick={() => setPage(p => p + 1)}>Next →</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
