import { useEffect, useMemo, useRef } from 'react'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import { toPng, toSvg } from 'html-to-image'

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
  if (normalized === 'FUNDAMENTA') return 'edge-fundamenta'
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
      minZoom: 0.15,
      maxZoom: 3.0,
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
            'border-color': '#1f2937',
            'transition-property': 'border-width, border-color, background-color',
            'transition-duration': '0.15s'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#2563eb',
            'background-color': '#dbeafe'
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
          selector: 'node.neighbor-highlight',
          style: {
            'border-width': 3,
            'border-color': '#6366f1',
            opacity: 1
          }
        },
        {
          selector: 'node.dimmed',
          style: {
            opacity: 0.25
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
            color: '#334155',
            'transition-property': 'opacity, line-color',
            'transition-duration': '0.15s'
          }
        },
        {
          selector: 'edge.dimmed',
          style: {
            opacity: 0.12
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
        },
        {
          selector: 'edge.edge-fundamenta',
          style: {
            width: 3,
            'line-style': 'dotted',
            'line-color': '#8b5cf6',
            'target-arrow-color': '#8b5cf6',
            'arrow-scale': 1.2
          }
        }
      ]
    })

    cy.on('tap', 'node', (event) => {
      const node = event.target.data('node')
      setSelectedNode(node)

      // Highlight neighbors
      cy.elements().removeClass('neighbor-highlight dimmed')
      const tapped = event.target
      const neighborhood = tapped.neighborhood().add(tapped)
      cy.elements().not(neighborhood).addClass('dimmed')
      neighborhood.nodes().addClass('neighbor-highlight')
    })

    // Double tap para adicionar à comparação
    cy.on('dbltap', 'node', (event) => {
      const node = event.target.data('node')
      // Aqui poderíamos emitir um evento ou chamar uma função para adicionar à comparação
      console.log('Nó adicionado para comparação:', node.name)
    })

    cy.on('tap', (event) => {
      if (event.target === cy) {
        cy.elements().removeClass('neighbor-highlight dimmed')
      }
    })

    cyRef.current = cy
    return () => {
      cy.destroy()
    }
  }, [elements, setSelectedNode])

  const onZoomIn = () => {
    if (!cyRef.current) return
    cyRef.current.zoom({ level: cyRef.current.zoom() * 1.3, renderedPosition: { x: containerRef.current.clientWidth / 2, y: containerRef.current.clientHeight / 2 } })
  }

  const onZoomOut = () => {
    if (!cyRef.current) return
    cyRef.current.zoom({ level: cyRef.current.zoom() / 1.3, renderedPosition: { x: containerRef.current.clientWidth / 2, y: containerRef.current.clientHeight / 2 } })
  }

  const onFit = () => {
    if (!cyRef.current) return
    cyRef.current.fit(undefined, 32)
  }

  const onResetView = () => {
    if (!cyRef.current) return
    cyRef.current.elements().removeClass('neighbor-highlight dimmed')
    cyRef.current.fit(undefined, 32)
    cyRef.current.center()
    setSelectedNode(null)
  }

  const onExportPNG = async () => {
    if (!containerRef.current) return
    try {
      const dataUrl = await toPng(containerRef.current, { quality: 0.95 })
      const link = document.createElement('a')
      link.download = 'grafo-computacao.png'
      link.href = dataUrl
      link.click()
    } catch (error) {
      console.error('Erro ao exportar PNG:', error)
    }
  }

  const onExportSVG = async () => {
    if (!containerRef.current) return
    try {
      const dataUrl = await toSvg(containerRef.current, { quality: 0.95 })
      const link = document.createElement('a')
      link.download = 'grafo-computacao.svg'
      link.href = dataUrl
      link.click()
    } catch (error) {
      console.error('Erro ao exportar SVG:', error)
    }
  }

  const onCenterSelected = () => {
    if (!cyRef.current || !selectedNode) return
    const sel = cyRef.current.getElementById(selectedNode.id)
    if (sel.length) {
      cyRef.current.animate({
        center: { eles: sel },
        zoom: 1.6,
        duration: 300
      })
    }
  }

  return (
    <section className="graph-board">
      <div className="graph-toolbar">
        <div className="toolbar-group">
          <button onClick={onZoomIn} title="Zoom in">+</button>
          <button onClick={onZoomOut} title="Zoom out">&minus;</button>
          <button onClick={onFit} title="Ajustar ao conteúdo">Ajustar</button>
          <button onClick={onResetView} title="Resetar visão">Resetar</button>
          {selectedNode && (
            <button onClick={onCenterSelected} title="Centralizar seleção">Centralizar</button>
          )}
          <button onClick={onExportPNG} title="Exportar como PNG">PNG</button>
          <button onClick={onExportSVG} title="Exportar como SVG">SVG</button>
        </div>
        <div className="toolbar-group">
          <span className="graph-legend">
            <span className="legend-dot" style={{ background: '#76bdf9' }} /> Pessoa
            <span className="legend-dot" style={{ background: '#8f6de8' }} /> Teoria
            <span className="legend-dot" style={{ background: '#5ccf84' }} /> Tecnologia
            <span className="legend-dot" style={{ background: '#f2cc60' }} /> Evento
          </span>
        </div>
      </div>
      <div className="graph-canvas" ref={containerRef} />
      <NodeDetailsDrawer node={selectedNode} onClose={() => {
        setSelectedNode(null)
        if (cyRef.current) cyRef.current.elements().removeClass('neighbor-highlight dimmed')
      }} />
    </section>
  )
}
