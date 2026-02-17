import { useState } from 'react'

import { useGraphContext } from '../state/GraphContext'

export default function SearchPanel() {
  const {
    runSearch,
    loadGraph,
    loadingGraph,
    loadingSearch,
    searchResult,
    error,
    setError
  } = useGraphContext()

  const [query, setQuery] = useState('Como as ideias de Newton chegaram à computação moderna?')
  const [uid, setUid] = useState('ev-003')

  const onSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await runSearch(query)
    } catch {
      // mantém fluxo para renderizar o grafo mesmo se a camada semântica falhar
    }
    if (uid.trim()) {
      try {
        await loadGraph(uid.trim())
      } catch {
        // erro já tratado no provider
      }
    }
  }

  const timing = searchResult?.timing

  return (
    <section className="search-panel">
      <form className="search-form" onSubmit={onSubmit}>
        <label>
          Pergunta histórica
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows={2}
            required
          />
        </label>

        <label>
          UID raiz do grafo
          <input
            value={uid}
            onChange={(event) => setUid(event.target.value)}
            placeholder="ex: ev-003"
          />
        </label>

        <button type="submit" disabled={loadingGraph || loadingSearch}>
          {loadingGraph || loadingSearch ? 'Processando...' : 'Buscar e Renderizar'}
        </button>
      </form>

      <div className="search-meta">
        {error ? <p className="error-text">Erro: {error}</p> : null}
        {searchResult?.answer ? (
          <>
            <h3>Resposta</h3>
            <p className="search-answer">{searchResult.answer}</p>
            {searchResult.sources?.length > 0 && (
              <div className="search-sources">
                <strong>Fontes:</strong>
                <ul>
                  {searchResult.sources.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            {timing && (
              <p className="search-timing muted">
                {timing.total_ms != null ? `Total: ${timing.total_ms}ms` : ''}
                {timing.embedding_ms != null ? ` | Embedding: ${timing.embedding_ms}ms` : ''}
                {timing.vector_search_ms != null ? ` | Vetorial: ${timing.vector_search_ms}ms` : ''}
                {timing.lineage_ms != null ? ` | Linhagem: ${timing.lineage_ms}ms` : ''}
                {timing.synthesis_ms != null ? ` | Síntese: ${timing.synthesis_ms}ms` : ''}
              </p>
            )}
          </>
        ) : (
          <p className="muted">Execute uma busca para destacar o caminho da resposta no grafo.</p>
        )}
      </div>
    </section>
  )
}
