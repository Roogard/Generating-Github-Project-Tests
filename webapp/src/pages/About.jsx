export default function About() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">About</h1>
          <div className="page-sub">Who I am and what GGPT is.</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-label">Intro</div>
        {/* TODO: write copy */}
        <p style={{ color: 'var(--text-3)' }}>(coming soon)</p>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-label">Project</div>
        {/* TODO: write copy */}
        <p style={{ color: 'var(--text-3)' }}>(coming soon)</p>
      </div>

      <div className="card">
        <div className="section-label">Contact</div>
        {/* TODO: write copy */}
        <p style={{ color: 'var(--text-3)' }}>(coming soon)</p>
      </div>
    </div>
  )
}
