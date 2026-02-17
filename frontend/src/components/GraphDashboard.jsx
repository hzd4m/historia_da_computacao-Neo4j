import { useEffect, useMemo, useRef } from 'react'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'

import { useGraphContext } from '../state/GraphContext'
import NodeDetailsDrawer from './NodeDetailsDrawer'

cytoscape.use(dagre)

const CATEGORY_STYLE = {
  Pessoa: { shape: 'ellipse', color: '#76bdf9' },
  Teoria: { shape: 'diamond', color: '#8f6de8' },
  Tecnologia: { shape: 'round-rectangle', color: '#5ccf84' },
  Evento: { shape: 'hexagon', color: '#f2cc60' },
  Entidade: { shape: 'round-rectangle', color: '#8fa1b3' }
}

function edgeClassFromType(relType) {
  const normalized = String(relType || '').toUpperCase()
  if (normalized === 'INFLUENCIA') return 'edge-influencia'
  if (normalized === 'EVOLUI_PARA') return 'edge-evolui'
  if (normalized === 'FEZ') return 'edge-fez'
  return 'edge-default'
}

export default function GraphDashboard() {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  const {
    graph,
    selectedNode,
    setSelectedNode,
    highlightNames
  } = useGraphContext()

  const elements = useMemo(() => {
    const names = highlightNames instanceof Set ? highlightNames : new Set()

    const nodes = graph.nodes.map((node) => {
      const stylePreset = CATEGORY_STYLE[node.category] || CATEGORY_STYLE.Entidade
      const classes = ['graph-node']
      if (names.has(node.name)) classes.push('answer-path-node')
      if (String(node.name).includes('Mother of All Demos') || String(node.description || '').includes('Mãe de Todas as Demonstrações')) {
        classes.push('engelbart-core')
      }
      return {
        data: {
          id: node.id,
          label: `${node.name}${node.year ? `\n${node.year}` : ''}`,
          category: node.category,
          shape: stylePreset.shape,
          color: stylePreset.color,
          node
        },
        classes: classes.join(' ')
      }
    })

    const edges = graph.edges
      .filter((edge) => edge.source && edge.target)
      .map((edge) => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.relType
        },
        classes: edgeClassFromType(edge.relType)
      }))

    return [...nodes, ...edges]
  }, [graph.edges, graph.nodes, highlightNames])

  useEffect(() => {
    if (!containerRef.current) return

    if (cyRef.current) {
      cyRef.current.destroy()
      cyRef.current = null
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 48,
        rankSep: 100,
        edgeSep: 24,
        fit: true,
        padding: 24,
        animate: true
      },
      wheelSensitivity: 0.2,
      minZoom: 0.25,
      maxZoom: 2.4,
      textureOnViewport: true,
      motionBlur: true,
      hideEdgesOnViewport: false,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            shape: 'data(shape)',
            'background-color': 'data(color)',
            color: '#0f172a',
            'font-size': 11,
            'text-wrap': 'wrap',
            'text-max-width': 130,
            'text-valign': 'center',
            'text-halign': 'center',
            width: 62,
            height: 62,
            'border-width': 2,
            'border-color': '#1f2937'
          }
        },
        {
          selector: 'node.answer-path-node',
          style: {
            'border-width': 5,
            'border-color': '#ff6a3d',
            'shadow-blur': 20,
            'shadow-color': '#ff6a3d',
            'shadow-opacity': 0.5
          }
        },
        {
          selector: 'node.engelbart-core',
          style: {
            'background-color': '#f59e0b',
            'border-width': 6,
            'border-color': '#7c2d12'
          }
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1,
            label: 'data(label)',
            'font-size': 9,
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.75,
            'text-background-padding': 2,
            'target-arrow-color': '#64748b',
            'line-color': '#64748b',
            color: '#334155'
          }
        },
        {
          selector: 'edge.edge-influencia',
          style: {
            'line-style': 'dashed',
            width: 3,
            'line-color': '#ef8f35',
            'target-arrow-color': '#ef8f35'
          }
        },
        {
          selector: 'edge.edge-evolui',
          style: {
            width: 4,
            'line-style': 'solid',
            'line-color': '#16a34a',
            'target-arrow-color': '#16a34a',
            'arrow-scale': 1.4
          }
        },
        {
          selector: 'edge.edge-fez',
          style: {
            width: 1.4,
            'line-style': 'solid',
            'line-color': '#64748b',
            'target-arrow-color': '#64748b'
          }
        }
      ]
    })

    cy.on('tap', 'node', (event) => {
      const node = event.target.data('node')
      setSelectedNode(node)
    })

    cyRef.current = cy
    return () => {
      cy.destroy()
    }
  }, [elements, setSelectedNode])

  const onResetView = () => {
    if (!cyRef.current) return
    cyRef.current.fit(undefined, 32)
    cyRef.current.center()
    cyRef.current.zoom(1)
  }

  return (
    <section className="graph-board">
      <div className="graph-toolbar">
        <button onClick={onResetView}>Resetar visão</button>
        <span className="muted">Zoom, pan e seleção ativos</span>
      </div>
      <div className="graph-canvas" ref={containerRef} />
      <NodeDetailsDrawer node={selectedNode} onClose={() => setSelectedNode(null)} />
    </section>
  )
}
