import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import RunsList from './pages/RunsList.jsx'
import RunDetail from './pages/RunDetail.jsx'
import Analytics from './pages/Analytics.jsx'
import Benchmark from './pages/Benchmark.jsx'

function Nav() {
  const link = ({ isActive }) => 'nav-link' + (isActive ? ' active' : '')
  return (
    <nav className="nav">
      <span className="nav-logo">
        <span className="nav-logo-dot" />
        GGPT
      </span>
      <NavLink className={link} to="/" end>Runs</NavLink>
      <NavLink className={link} to="/benchmark">Benchmark</NavLink>
      <NavLink className={link} to="/analytics">Analytics</NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<RunsList />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/benchmark" element={<Benchmark />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </BrowserRouter>
  )
}
