import GraphDashboard from './components/GraphDashboard'
import SearchPanel from './components/SearchPanel'
import TimelineStoryline from './components/TimelineStoryline'
import Tooltip from './components/Tooltip'
import AdvancedFilters from './components/AdvancedFilters'
import LineageComparison from './components/LineageComparison'
import Notifications from './components/Notifications'
import { useEffect, useState } from 'react'

export default function App() {
  const [theme, setTheme] = useState('light')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    setTheme(savedTheme)
    document.documentElement.setAttribute('data-theme', savedTheme)
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <div className="app-shell">
      <Tooltip content={theme === 'light' ? 'Alternar para modo escuro' : 'Alternar para modo claro'}>
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
      </Tooltip>
      <header className="app-header">
        <div>
          <p className="eyebrow">Graph Data Computer</p>
          <h1>Linhagem Histórica da Computação</h1>
        </div>
      </header>
      <SearchPanel />
      <TimelineStoryline />
      <AdvancedFilters />
      <LineageComparison />
      <GraphDashboard />
      <Notifications />
    </div>
  )
}
