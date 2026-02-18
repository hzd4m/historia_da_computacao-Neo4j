import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import WordCloudVisualization from '../components/WordCloudVisualization'

// Mock the useGraphContext hook
vi.mock('../state/GraphContext', async () => {
  return {
    useGraphContext: () => ({
      originalGraph: {
        nodes: [
          { id: '1', name: 'Computador', category: 'Tecnologia', description: 'Dispositivo eletrônico' },
          { id: '2', name: 'Algoritmo', category: 'Teoria', description: 'Sequência de instruções' },
          { id: '3', name: 'Programação', category: 'Tecnologia', description: 'Criação de software' }
        ],
        edges: []
      }
    })
  }
})

describe('WordCloudVisualization', () => {
  it('renders without crashing', () => {
    render(<WordCloudVisualization />)
    expect(screen.getByText('Nuvem de Palavras dos Conteúdos')).toBeInTheDocument()
  })

  it('displays filter controls', () => {
    render(<WordCloudVisualization />)
    expect(screen.getByText('Filtrar por Categoria:')).toBeInTheDocument()
  })

  it('shows word cloud container', () => {
    render(<WordCloudVisualization />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })
})