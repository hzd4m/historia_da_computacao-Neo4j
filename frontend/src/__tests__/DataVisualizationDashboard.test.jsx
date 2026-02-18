import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DataVisualizationDashboard from '../components/DataVisualizationDashboard'

// Mock all visualization components
vi.mock('../components/CategoryTimeline', async () => {
  return {
    default: () => <div data-testid="category-timeline">Category Timeline Component</div>
  }
})

vi.mock('../components/GeographicDistribution', async () => {
  return {
    default: () => <div data-testid="geographic-distribution">Geographic Distribution Component</div>
  }
})

vi.mock('../components/InnovationTimeline', async () => {
  return {
    default: () => <div data-testid="innovation-timeline">Innovation Timeline Component</div>
  }
})

vi.mock('../components/NetworkMetrics', async () => {
  return {
    default: () => <div data-testid="network-metrics">Network Metrics Component</div>
  }
})

vi.mock('../components/WordCloudVisualization', async () => {
  return {
    default: () => <div data-testid="word-cloud">Word Cloud Component</div>
  }
})

describe('DataVisualizationDashboard', () => {
  it('renders without crashing', () => {
    render(<DataVisualizationDashboard />)
    expect(screen.getByText('Dashboard de Visualizações')).toBeInTheDocument()
  })

  it('displays all tab buttons', () => {
    render(<DataVisualizationDashboard />)
    expect(screen.getByText('Categorias')).toBeInTheDocument()
    expect(screen.getByText('Geografia')).toBeInTheDocument()
    expect(screen.getByText('Linha do Tempo')).toBeInTheDocument()
    expect(screen.getByText('Métricas de Rede')).toBeInTheDocument()
    expect(screen.getByText('Nuvem de Palavras')).toBeInTheDocument()
  })

  it('shows category timeline by default', () => {
    render(<DataVisualizationDashboard />)
    expect(screen.getByTestId('category-timeline')).toBeInTheDocument()
  })
})