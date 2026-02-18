import { useState } from 'react'
import CategoryTimeline from './CategoryTimeline'
import GeographicDistribution from './GeographicDistribution'
import InnovationTimeline from './InnovationTimeline'
import NetworkMetrics from './NetworkMetrics'
import WordCloudVisualization from './WordCloudVisualization'

export default function DataVisualizationDashboard() {
  const [activeTab, setActiveTab] = useState('category')

  const tabs = [
    { id: 'category', label: 'Categorias', component: CategoryTimeline },
    { id: 'geographic', label: 'Geografia', component: GeographicDistribution },
    { id: 'timeline', label: 'Linha do Tempo', component: InnovationTimeline },
    { id: 'network', label: 'Métricas de Rede', component: NetworkMetrics },
    { id: 'wordcloud', label: 'Nuvem de Palavras', component: WordCloudVisualization }
  ]

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || CategoryTimeline

  return (
    <div className="dashboard-container">
      <h2>Dashboard de Visualizações</h2>
      
      <div className="dashboard-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      <div className="dashboard-content">
        <ActiveComponent />
      </div>
    </div>
  )
}