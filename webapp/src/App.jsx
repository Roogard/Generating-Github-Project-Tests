import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import About from './pages/About.jsx'
import Installation from './pages/Installation.jsx'
import Database from './pages/Database.jsx'
import RunDetail from './pages/RunDetail.jsx'

function Nav() {
  const link = ({ isActive }) => 'nav-link' + (isActive ? ' active' : '')
  return (
    <nav className="nav">
      <span className="nav-logo">
        <span className="nav-logo-dot" />
        GGPT
      </span>
      <NavLink className={link} to="/" end>About</NavLink>
      <NavLink className={link} to="/installation">Installation</NavLink>
      <NavLink className={link} to="/database">Database</NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<About />} />
        <Route path="/installation" element={<Installation />} />
        <Route path="/database" element={<Database />} />
        <Route path="/runs/:id" element={<RunDetail />} />
      </Routes>
    </BrowserRouter>
  )
}
