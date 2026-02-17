import GraphDashboard from './components/GraphDashboard'
import SearchPanel from './components/SearchPanel'

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Graph Data Computer</p>
          <h1>Linhagem Histórica da Computação</h1>
        </div>
      </header>
      <SearchPanel />
      <GraphDashboard />
    </div>
  )
}
