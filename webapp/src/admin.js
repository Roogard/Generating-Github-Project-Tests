// Client-side admin-mode state. No server-side verification of the key —
// the backend rejects every admin-gated request whose X-Admin-Key header
// doesn't match `GGPT_ADMIN_KEY`, so a wrong key simply 403s on first use.
import { useEffect, useState } from 'react'

const STORAGE_KEY = 'ggpt_admin'

const listeners = new Set()

export function isAdmin() {
  return !!getAdminKey()
}

export function useAdmin() {
  const [admin, setAdmin] = useState(isAdmin())
  useEffect(() => subscribeAdmin(setAdmin), [])
  return admin
}

export const BENCHMARK_MODES = ['quixbugs']
export const isBenchmarkMode = mode => BENCHMARK_MODES.includes(mode)

export function getAdminKey() {
  try {
    return localStorage.getItem(STORAGE_KEY) || null
  } catch {
    return null
  }
}

export function enterAdminMode(key) {
  const trimmed = (key || '').trim()
  if (!trimmed) return false
  localStorage.setItem(STORAGE_KEY, trimmed)
  notify()
  return true
}

export function exitAdminMode() {
  localStorage.removeItem(STORAGE_KEY)
  notify()
}

export function subscribeAdmin(cb) {
  listeners.add(cb)
  return () => listeners.delete(cb)
}

function notify() {
  for (const cb of listeners) {
    try { cb(isAdmin()) } catch { /* ignore */ }
  }
}

// Cross-tab sync
if (typeof window !== 'undefined') {
  window.addEventListener('storage', e => {
    if (e.key === STORAGE_KEY) notify()
  })
}
