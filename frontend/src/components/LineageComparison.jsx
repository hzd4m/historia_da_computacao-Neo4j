import { useState } from 'react'
import { useGraphContext } from '../state/GraphContext'

export default function LineageComparison() {
  const { originalGraph } = useGraphContext()
  const [comparing, setComparing] = useState(false)
  const [comparisonGraphs, setComparisonGraphs] = useState([])
  const [selectedNodes, setSelectedNodes] = useState([])

  // Função para iniciar comparação
  const startComparison = () => {
    setComparing(true)
    setComparisonGraphs([])
    setSelectedNodes([])
  }

  // Função para adicionar nó à comparação
  const addToComparison = (node) => {
    if (!selectedNodes.find(n => n.id === node.id)) {
      setSelectedNodes([...selectedNodes, node])
    }
  }

  // Função para remover nó da comparação
  const removeFromComparison = (nodeId) => {
    setSelectedNodes(selectedNodes.filter(n => n.id !== nodeId))
  }

  // Função para limpar comparação
  const clearComparison = () => {
    setSelectedNodes([])
    setComparisonGraphs([])
    setComparing(false)
  }

  // Função para gerar grafo de comparação
  const generateComparisonGraph = () => {
    if (selectedNodes.length < 2) return

    // Criar novo grafo com nós selecionados e suas conexões
    const nodeIds = new Set(selectedNodes.map(n => n.id))
    const comparisonNodes = [...selectedNodes]
    
    // Encontrar arestas que conectam os nós selecionados
    const comparisonEdges = originalGraph.edges.filter(edge => 
      nodeIds.has(edge.source) && nodeIds.has(edge.target)
    )

    setComparisonGraphs([{
      id: `comparison-${Date.now()}`,
      nodes: comparisonNodes,
      edges: comparisonEdges,
      createdAt: new Date().toISOString()
    }])
  }

  if (!comparing) {
    return (
      <div className="lineage-comparison">
        <button onClick={startComparison} className="comparison-button">
          Comparar Linhagens
        </button>
      </div>
    )
  }

  return (
    <div className="lineage-comparison comparison-active">
      <div className="comparison-header">
        <h3>Comparação de Linhagens</h3>
        <div className="comparison-actions">
          <button onClick={generateComparisonGraph} disabled={selectedNodes.length < 2}>
            Gerar Comparação
          </button>
          <button onClick={clearComparison}>Cancelar</button>
        </div>
      </div>
      
      <div className="comparison-selection">
        <h4>Nós Selecionados ({selectedNodes.length})</h4>
        {selectedNodes.length === 0 ? (
          <p>Selecione nós no grafo para comparar</p>
        ) : (
          <div className="selected-nodes">
            {selectedNodes.map(node => (
              <div key={node.id} className="selected-node">
                <span className="node-name">{node.name}</span>
                <span className="node-category">{node.category}</span>
                <button 
                  onClick={() => removeFromComparison(node.id)}
                  className="remove-node"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {comparisonGraphs.length > 0 && (
        <div className="comparison-results">
          <h4>Resultado da Comparação</h4>
          {comparisonGraphs.map(graph => (
            <div key={graph.id} className="comparison-graph">
              <p>Grafo gerado com {graph.nodes.length} nós e {graph.edges.length} conexões</p>
              <small>Criado em: {new Date(graph.createdAt).toLocaleString()}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}