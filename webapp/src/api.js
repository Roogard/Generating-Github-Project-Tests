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

// Runs — single endpoint, dispatched by `source` field on the body.
// Body shape: { source: 'repo' | 'swtbench', ...source-specific fields }
export const getRuns = (status) => req('GET', `/runs/${status ? `?status=${status}` : ''}`)
export const getRun = (id) => req('GET', `/runs/${id}`)
export const getRunStatus = (id) => req('GET', `/runs/${id}/status`)
export const createRun = (body) => req('POST', '/runs/', body)
export const deleteRun = (id) => req('DELETE', `/runs/${id}`)
export const downloadRun = (id) => window.open(BASE + `/runs/${id}/download`, '_blank')

// Analytics
export const getAnalyticsSummary = () => req('GET', '/analytics/summary')
