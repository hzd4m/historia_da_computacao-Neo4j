import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import GeographicDistribution from '../components/GeographicDistribution'

// Mock the useGraphContext hook
vi.mock('../state/GraphContext', async () => {
  return {
    useGraphContext: () => ({
      originalGraph: {
        nodes: [
          { id: '1', name: 'Node 1', category: 'Pessoa', year: 1950, nacionalidade: 'Brasil' },
          { id: '2', name: 'Node 2', category: 'Tecnologia', year: 1960, nacionalidade: 'EUA' },
          { id: '3', name: 'Node 3', category: 'Pessoa', year: 1970, nacionalidade: 'Brasil' }
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
    ComposedChart: ({ children }) => <div data-testid="composed-chart">{children}</div>,
    Bar: () => <div data-testid="bar" />,
    Scatter: () => <div data-testid="scatter" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
    Legend: () => <div data-testid="legend" />,
    ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>
  }
})

describe('GeographicDistribution', () => {
  it('renders without crashing', () => {
    render(<GeographicDistribution />)
    expect(screen.getByText('Distribuição Geográfica de Contribuições')).toBeInTheDocument()
  })

  it('displays chart containers', () => {
    render(<GeographicDistribution />)
    expect(screen.getByTestId('composed-chart')).toBeInTheDocument()
  })

  it('shows timeline heading', () => {
    render(<GeographicDistribution />)
    expect(screen.getByText('Linha do Tempo por País')).toBeInTheDocument()
  })
})