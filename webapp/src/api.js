const BASE = '/api'

async function req(method, path, body) {
  const opts = { method, headers: {} }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return null
  return res.json()
}

// Runs
export const getRuns = (status) => req('GET', `/runs${status ? `?status=${status}` : ''}`)
export const getRun = (id) => req('GET', `/runs/${id}`)
export const getRunStatus = (id) => req('GET', `/runs/${id}/status`)
export const createRun = (body) => req('POST', '/runs/', body)
export const deleteRun = (id) => req('DELETE', `/runs/${id}`)
export const downloadRun = (id) => window.open(BASE + `/runs/${id}/download`, '_blank')

// DB
export const getDbTables = () => req('GET', '/db/tables')
export const getDbRows = (table, page = 1, limit = 50, filterCol = '', filterVal = '') => {
  let qs = `?page=${page}&limit=${limit}`
  if (filterCol) qs += `&filter_col=${filterCol}&filter_val=${encodeURIComponent(filterVal)}`
  return req('GET', `/db/${table}${qs}`)
}
export const dbQuery = (sql) => req('POST', '/db/query', { sql })
export const dbCreate = (table, data) => req('POST', `/db/${table}`, data)
export const dbUpdate = (table, id, data) => req('PUT', `/db/${table}/${id}`, data)
export const dbDelete = (table, id) => req('DELETE', `/db/${table}/${id}`)

// VectorDB
export const getVectorStats = () => req('GET', '/vectordb/stats')
export const vectorSearch = (query, testType, n) => req('POST', '/vectordb/search', { query, test_type: testType, n })
export const getVectorExamples = (page = 1, limit = 20, testType = '') =>
  req('GET', `/vectordb/examples?page=${page}&limit=${limit}${testType ? `&test_type=${testType}` : ''}`)
export const deleteVectorExample = (id) => req('DELETE', `/vectordb/examples/${encodeURIComponent(id)}`)
