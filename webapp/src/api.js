import { getAdminKey, exitAdminMode } from './admin.js'

const BASE = '/api'

export class AdminKeyRejected extends Error {
  constructor(msg = 'Admin key rejected') {
    super(msg)
    this.name = 'AdminKeyRejected'
  }
}

async function req(method, path, body) {
  const opts = { method, headers: {} }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const adminKey = getAdminKey()
  if (adminKey) opts.headers['X-Admin-Key'] = adminKey

  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    if (res.status === 403 && adminKey) {
      exitAdminMode()
      throw new AdminKeyRejected(err.detail || 'Admin key rejected')
    }
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
export const promoteRunToMemory = (id, body = {}) => req('POST', `/runs/${id}/promote-to-memory`, body)

// Admin-only
export const createBenchmark = (body) => req('POST', '/runs/benchmark', body)

// VectorDB (read-only browser + similarity search)
export const getVectorStats = () => req('GET', '/vectordb/stats')
export const vectorSearch = (query, testType, n) => req('POST', '/vectordb/search', { query, test_type: testType, n })
export const getVectorExamples = (page = 1, limit = 20, testType = '') =>
  req('GET', `/vectordb/examples?page=${page}&limit=${limit}${testType ? `&test_type=${testType}` : ''}`)

// Analytics
export const getAnalyticsSummary = () => req('GET', '/analytics/summary')
