import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import InnovationTimeline from '../components/InnovationTimeline'

// Mock the useGraphContext hook
vi.mock('../state/GraphContext', async () => {
  return {
    useGraphContext: () => ({
      originalGraph: {
        nodes: [
          { id: '1', name: 'Node 1', category: 'Pessoa', year: 1950 },
          { id: '2', name: 'Node 2', category: 'Tecnologia', year: 1960 },
          { id: '3', name: 'Node 3', category: 'Pessoa', year: 1970 }
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
    LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
    AreaChart: ({ children }) => <div data-testid="area-chart">{children}</div>,
    Line: () => <div data-testid="line" />,
    Area: () => <div data-testid="area" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
    Legend: () => <div data-testid="legend" />,
    ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>
  }
})

describe('InnovationTimeline', () => {
  it('renders without crashing', () => {
    render(<InnovationTimeline />)
    expect(screen.getByText('Inovações ao Longo do Tempo')).toBeInTheDocument()
  })

  it('displays chart containers', () => {
    render(<InnovationTimeline />)
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByTestId('area-chart')).toBeInTheDocument()
  })

  it('shows cumulative growth heading', () => {
    render(<InnovationTimeline />)
    expect(screen.getByText('Crescimento Cumulativo')).toBeInTheDocument()
  })
})