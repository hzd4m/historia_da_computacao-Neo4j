import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import CategoryTimeline from '../components/CategoryTimeline'

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

describe('CategoryTimeline', () => {
  it('renders without crashing', () => {
    render(<CategoryTimeline />)
    // Just check that the component renders without throwing an error
    expect(true).toBe(true)
  })
})