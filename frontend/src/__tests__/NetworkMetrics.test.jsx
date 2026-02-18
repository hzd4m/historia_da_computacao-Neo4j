import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import NetworkMetrics from '../components/NetworkMetrics'

// Mock the useGraphContext hook
vi.mock('../state/GraphContext', async () => {
  return {
    useGraphContext: () => ({
      originalGraph: {
        nodes: [
          { id: '1', name: 'Node 1', category: 'Pessoa' },
          { id: '2', name: 'Node 2', category: 'Tecnologia' },
          { id: '3', name: 'Node 3', category: 'Pessoa' }
        ],
        edges: [
          { id: 'e1', source: '1', target: '2' },
          { id: 'e2', source: '2', target: '3' }
        ]
      }
    })
  }
})

// Mock recharts components
vi.mock('recharts', async () => {
  const ActualRecharts = await vi.importActual('recharts')
  return {
    ...ActualRecharts,
    RadarChart: ({ children }) => <div data-testid="radar-chart">{children}</div>,
    RadialBarChart: ({ children }) => <div data-testid="radial-bar-chart">{children}</div>,
    Radar: () => <div data-testid="radar" />,
    RadialBar: () => <div data-testid="radial-bar" />,
    PolarGrid: () => <div data-testid="polar-grid" />,
    PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
    PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
    Tooltip: () => <div data-testid="tooltip" />,
    Legend: () => <div data-testid="legend" />,
    ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>
  }
})

describe('NetworkMetrics', () => {
  it('renders without crashing', () => {
    render(<NetworkMetrics />)
    expect(screen.getByText('Métricas da Rede')).toBeInTheDocument()
  })

  it('displays chart containers', () => {
    render(<NetworkMetrics />)
    expect(screen.getByTestId('radar-chart')).toBeInTheDocument()
    expect(screen.getByTestId('radial-bar-chart')).toBeInTheDocument()
  })

  it('shows node centrality heading', () => {
    render(<NetworkMetrics />)
    expect(screen.getByText('Centralidade dos Nós Principais')).toBeInTheDocument()
  })
})