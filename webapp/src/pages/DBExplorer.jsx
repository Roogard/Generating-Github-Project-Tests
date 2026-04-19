import { useEffect, useState } from 'react'
import { getDbTables, getDbRows, dbQuery } from '../api.js'

function SqlQueryBox({ onResult }) {
  const [sql, setSql] = useState('SELECT * FROM runs LIMIT 20')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await dbQuery(sql)
      onResult(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 14, marginBottom: 10 }}>SQL Query</h3>
      <textarea
        rows={4}
        value={sql}
        onChange={e => setSql(e.target.value)}
        style={{ marginBottom: 10, fontFamily: 'monospace' }}
      />
      {error && <div className="alert alert-error" style={{ marginBottom: 8 }}>{error}</div>}
      <button className="btn-primary" onClick={run} disabled={loading}>
        {loading ? 'Running...' : 'Run Query'}
      </button>
    </div>
  )
}

function ResultTable({ columns, rows }) {
  if (!columns.length) return null
  return (
    <div className="card" style={{ padding: 0, overflow: 'auto' }}>
      <table>
        <thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map(c => (
                <td key={c} style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {String(row[c] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <p style={{ padding: 16, color: '#64748b', textAlign: 'center' }}>No rows returned.</p>
      )}
    </div>
  )
}

export default function DBExplorer() {
  const [tables, setTables] = useState([])
  const [selectedTable, setSelectedTable] = useState('')
  const [rows, setRows] = useState([])
  const [columns, setColumns] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filterCol, setFilterCol] = useState('')
  const [filterVal, setFilterVal] = useState('')
  const [queryResult, setQueryResult] = useState(null)
  const [error, setError] = useState('')
  const LIMIT = 50

  useEffect(() => {
    getDbTables().then(t => {
      setTables(t)
      if (t.length > 0) setSelectedTable(t[0].table)
    }).catch(e => setError(e.message))
  }, [])

  const loadRows = () => {
    if (!selectedTable) return
    getDbRows(selectedTable, page, LIMIT, filterCol, filterVal)
      .then(r => { setRows(r.rows); setColumns(r.columns.map(c => ({ name: c }))); setTotal(r.total) })
      .catch(e => setError(e.message))
  }

  useEffect(() => { setPage(1) }, [selectedTable, filterCol, filterVal])
  useEffect(() => { loadRows() }, [selectedTable, page, filterCol, filterVal])

  const tableMeta = tables.find(t => t.table === selectedTable)

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Database Explorer</h1>
        <span style={{ color: '#64748b', fontSize: 13 }}>SQLite — ghtest.db</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <SqlQueryBox onResult={setQueryResult} />

      {queryResult && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <h3 style={{ fontSize: 14 }}>Query Results ({queryResult.rows.length} rows)</h3>
            <button className="btn-ghost btn-sm" onClick={() => setQueryResult(null)}>✕ Clear</button>
          </div>
          <ResultTable columns={queryResult.columns} rows={queryResult.rows} />
        </div>
      )}

      <div className="split">
        <div className="split-left">
          <h3 style={{ fontSize: 13, color: '#64748b', marginBottom: 8, textTransform: 'uppercase' }}>Tables</h3>
          <div className="card" style={{ padding: 0 }}>
            {tables.map(t => (
              <div
                key={t.table}
                onClick={() => setSelectedTable(t.table)}
                style={{
                  padding: '10px 14px', cursor: 'pointer',
                  display: 'flex', justifyContent: 'space-between',
                  borderBottom: '1px solid #334155',
                  background: selectedTable === t.table ? '#0f1f38' : 'transparent',
                  fontSize: 14,
                }}
              >
                <span style={{ fontFamily: 'monospace' }}>{t.table}</span>
                <span style={{ color: '#64748b', fontSize: 12 }}>{t.row_count}</span>
              </div>
            ))}
          </div>
          <p style={{ marginTop: 12, fontSize: 12, color: '#475569', lineHeight: 1.5 }}>
            For full CRUD operations, open <strong>ghtest.db</strong> in DB Browser for SQLite or use the API at <code>/docs</code>.
          </p>
        </div>

        <div className="split-right">
          {selectedTable && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <h2 style={{ fontSize: 16, fontFamily: 'monospace' }}>{selectedTable}</h2>
                <span style={{ fontSize: 13, color: '#64748b' }}>{total} rows</span>
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <select
                  style={{ width: 160 }}
                  value={filterCol}
                  onChange={e => setFilterCol(e.target.value)}
                >
                  <option value="">Filter column...</option>
                  {(tableMeta?.columns || []).map(c => (
                    <option key={c.name} value={c.name}>{c.name}</option>
                  ))}
                </select>
                <input
                  placeholder="Filter value..."
                  value={filterVal}
                  onChange={e => setFilterVal(e.target.value)}
                  style={{ flex: 1 }}
                />
              </div>

              <div className="card" style={{ padding: 0, overflow: 'auto', marginBottom: 12 }}>
                <table>
                  <thead>
                    <tr>{columns.map(c => <th key={c.name}>{c.name}</th>)}</tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={i}>
                        {columns.map(c => (
                          <td key={c.name} style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                            {String(row[c.name] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                    {rows.length === 0 && (
                      <tr><td colSpan={columns.length} style={{ textAlign: 'center', color: '#64748b', padding: 24 }}>No rows</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13, color: '#64748b' }}>
                <button className="btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                <span>Page {page} of {Math.ceil(total / LIMIT) || 1}</span>
                <button className="btn-ghost btn-sm" disabled={page * LIMIT >= total} onClick={() => setPage(p => p + 1)}>Next →</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
