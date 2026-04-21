import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import RunsList from './pages/RunsList.jsx'
import NewRun from './pages/NewRun.jsx'
import RunDetail from './pages/RunDetail.jsx'
import BenchmarkRun from './pages/BenchmarkRun.jsx'
import Analytics from './pages/Analytics.jsx'
import VectorDB from './pages/VectorDB.jsx'
import AdminToggle from './components/AdminToggle.jsx'
import { useAdmin } from './admin.js'

function Nav() {
  const link = ({ isActive }) => 'nav-link' + (isActive ? ' active' : '')
  const admin = useAdmin()
  return (
    <nav className="nav" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <span className="nav-logo">GGPT</span>
      <NavLink className={link} to="/" end>Runs</NavLink>
      <NavLink className={link} to="/analytics">Analytics</NavLink>
      <NavLink className={link} to="/vectordb">Vector DB</NavLink>
      {admin && <NavLink className={link} to="/runs/benchmark">Benchmark</NavLink>}
      <AdminToggle />
    </nav>
  )
}

function AdminOnly({ children }) {
  const admin = useAdmin()
  return admin ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<RunsList />} />
        <Route path="/runs/new" element={<NewRun />} />
        <Route path="/runs/benchmark" element={<AdminOnly><BenchmarkRun /></AdminOnly>} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/vectordb" element={<VectorDB />} />
      </Routes>
    </BrowserRouter>
  )
}
