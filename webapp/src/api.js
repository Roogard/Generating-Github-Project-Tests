const BASE = '/api'

async function req(method, path) {
  const res = await fetch(BASE + path, { method })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

// Read-only run endpoints — used by RunDetail when drilling into one issue
// from the Database tab. Run creation lives in the GitHub Action.
export const getRun = (id) => req('GET', `/runs/${id}`)
export const getRunStatus = (id) => req('GET', `/runs/${id}/status`)
export const downloadRun = (id) => window.open(BASE + `/runs/${id}/download`, '_blank')

// The featured benchmark batch shown on /database.
export const getFeaturedBatch = () => req('GET', '/database/featured-batch')
