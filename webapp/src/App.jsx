import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import RunsList from './pages/RunsList.jsx'
import NewRun from './pages/NewRun.jsx'
import RunDetail from './pages/RunDetail.jsx'
import Analytics from './pages/Analytics.jsx'
import DBExplorer from './pages/DBExplorer.jsx'
import VectorDB from './pages/VectorDB.jsx'

function Nav() {
  const link = ({ isActive }) => 'nav-link' + (isActive ? ' active' : '')
  return (
    <nav className="nav">
      <span className="nav-logo">GHTest</span>
      <NavLink className={link} to="/" end>Runs</NavLink>
      <NavLink className={link} to="/analytics">Analytics</NavLink>
      <NavLink className={link} to="/db">Database</NavLink>
      <NavLink className={link} to="/vectordb">Vector DB</NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<RunsList />} />
        <Route path="/runs/new" element={<NewRun />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/db" element={<DBExplorer />} />
        <Route path="/vectordb" element={<VectorDB />} />
      </Routes>
    </BrowserRouter>
  )
}
