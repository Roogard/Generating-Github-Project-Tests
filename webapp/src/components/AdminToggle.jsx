import { useState } from 'react'
import { useAdmin, enterAdminMode, exitAdminMode } from '../admin.js'

// Tiny nav widget: "Enter admin mode" button that flips into a passphrase
// input, or an "Admin ON — exit" pill when admin mode is active.
//
// The key is stored client-side only; there's no server-side verification
// on entry. The first admin-gated API call is what validates it — if wrong,
// api.js clears the stored key and throws AdminKeyRejected.
export default function AdminToggle() {
  const admin = useAdmin()
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState('')

  const submit = e => {
    e.preventDefault()
    if (enterAdminMode(value)) {
      setValue('')
      setEditing(false)
    }
  }

  if (admin) {
    return (
      <button
        className="btn-ghost btn-sm"
        onClick={exitAdminMode}
        style={{
          marginLeft: 'auto',
          background: '#14532d',
          borderColor: '#22c55e',
          color: '#bbf7d0',
          fontSize: 12,
        }}
        title="Click to exit admin mode"
      >
        Admin ON · exit
      </button>
    )
  }

  if (editing) {
    return (
      <form onSubmit={submit} style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
        <input
          type="password"
          autoFocus
          placeholder="admin key"
          value={value}
          onChange={e => setValue(e.target.value)}
          onBlur={() => { if (!value) setEditing(false) }}
          style={{ width: 140, fontSize: 12, padding: '4px 8px' }}
        />
        <button type="submit" className="btn-primary btn-sm" style={{ fontSize: 12 }}>Enter</button>
      </form>
    )
  }

  return (
    <button
      className="btn-ghost btn-sm"
      onClick={() => setEditing(true)}
      style={{ marginLeft: 'auto', fontSize: 12 }}
    >
      Enter admin mode
    </button>
  )
}
