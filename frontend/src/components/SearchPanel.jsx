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
            <h3>Resposta atual</h3>
            <p>{searchResult.answer}</p>
          </>
        ) : (
          <p className="muted">Execute uma busca para destacar o caminho da resposta no grafo.</p>
        )}
      </div>
    </section>
  )
}
