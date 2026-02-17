import { createContext, useCallback, useContext, useMemo, useState } from 'react'

import { fetchGraph, searchHybrid } from '../api/client'

const GraphContext = createContext(null)

function normalizeNode(rawNode, idx) {
  const id = String(
    rawNode.id ||
      rawNode.uid ||
      rawNode.nome ||
      rawNode.titulo ||
      `node-${idx}`
  )
  const category = rawNode.category || rawNode.type || rawNode.label || rawNode.kind || 'Entidade'
  const name = rawNode.nome || rawNode.titulo || rawNode.name || rawNode.id || id
  return {
    ...rawNode,
    id,
    category,
    name,
    year: rawNode.ano ?? rawNode.ano_proposta ?? rawNode.year ?? null,
    description: rawNode.descricao || rawNode.bio || rawNode.impacto || rawNode.problema_resolvido || 'Sem descrição disponível.',
    sourceLinks: rawNode.fontes || rawNode.sources || []
  }
}

function normalizeEdge(rawEdge, idx) {
  return {
    ...rawEdge,
    id: String(rawEdge.id || `edge-${idx}`),
    source: String(rawEdge.source || rawEdge.from || rawEdge.from_id || rawEdge.start),
    target: String(rawEdge.target || rawEdge.to || rawEdge.to_id || rawEdge.end),
    relType: String(rawEdge.rel_type || rawEdge.type || rawEdge.relationship || 'REL')
  }
}

function extractHighlightedNames(payload) {
  const names = new Set()
  const sources = Array.isArray(payload?.sources) ? payload.sources : []
  const lineage = Array.isArray(payload?.lineage) ? payload.lineage : []

  const collectFromText = (text) => {
    if (!text || typeof text !== 'string') return
    text
      .split('->')
      .map((part) => part.trim().replace(/\(\d{4}\)/g, '').trim())
      .filter(Boolean)
      .forEach((item) => names.add(item))
  }

  sources.forEach(collectFromText)
  lineage.forEach(collectFromText)

  return names
}

export function GraphProvider({ children }) {
  const [graph, setGraph] = useState({ nodes: [], edges: [] })
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchResult, setSearchResult] = useState(null)
  const [highlightNames, setHighlightNames] = useState(new Set())
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [loadingSearch, setLoadingSearch] = useState(false)
  const [error, setError] = useState('')

  const runSearch = useCallback(async (query) => {
    setLoadingSearch(true)
    setError('')
    try {
      const result = await searchHybrid(query)
      setSearchResult(result)
      setHighlightNames(extractHighlightedNames(result))
      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setError(message)
      throw err
    } finally {
      setLoadingSearch(false)
    }
  }, [])

  const loadGraph = useCallback(async (uid) => {
    if (!uid) return
    setLoadingGraph(true)
    setError('')
    try {
      const payload = await fetchGraph(uid)
      const rawNodes = Array.isArray(payload.nodes) ? payload.nodes : []
      const rawEdges = Array.isArray(payload.edges) ? payload.edges : []
      setGraph({
        nodes: rawNodes.map(normalizeNode),
        edges: rawEdges.map(normalizeEdge)
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setError(message)
      throw err
    } finally {
      setLoadingGraph(false)
    }
  }, [])

  const value = useMemo(
    () => ({
      graph,
      selectedNode,
      setSelectedNode,
      searchResult,
      highlightNames,
      runSearch,
      loadGraph,
      loadingGraph,
      loadingSearch,
      error,
      setError
    }),
    [
      error,
      graph,
      highlightNames,
      loadGraph,
      loadingGraph,
      loadingSearch,
      runSearch,
      searchResult,
      selectedNode
    ]
  )

  return <GraphContext.Provider value={value}>{children}</GraphContext.Provider>
}

export function useGraphContext() {
  const ctx = useContext(GraphContext)
  if (!ctx) {
    throw new Error('useGraphContext deve ser usado dentro de GraphProvider')
  }
  return ctx
}
