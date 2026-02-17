import { useEffect, useState } from 'react'

import { fetchTimeline } from '../api/client'
import { useGraphContext } from '../state/GraphContext'

export default function TimelineStoryline() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(true)
  const { loadGraph } = useGraphContext()

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchTimeline()
      .then((data) => {
        if (!cancelled && Array.isArray(data)) {
          setEvents(data)
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const onEventClick = (uid) => {
    loadGraph(uid).catch(() => {})
  }

  if (!expanded) {
    return (
      <section className="timeline-section timeline-collapsed">
        <button className="timeline-toggle" onClick={() => setExpanded(true)}>
          Storyline temporal
        </button>
      </section>
    )
  }

  return (
    <section className="timeline-section">
      <div className="timeline-header">
        <h2>Storyline Temporal</h2>
        <button className="timeline-toggle" onClick={() => setExpanded(false)}>
          Recolher
        </button>
      </div>

      {loading && <p className="muted">Carregando linha do tempo...</p>}

      {!loading && events.length === 0 && (
        <p className="muted">Nenhum evento disponível na timeline.</p>
      )}

      <div className="timeline-track">
        {events.map((evt, idx) => (
          <button
            key={evt.uid}
            className="timeline-event"
            onClick={() => onEventClick(evt.uid)}
            title={evt.descricao || evt.titulo}
          >
            <span className="timeline-year">{evt.ano ?? '?'}</span>
            <span className="timeline-title">{evt.titulo}</span>
            {evt.tecnologia_base && (
              <span className="timeline-tech muted">{evt.tecnologia_base}</span>
            )}
            {idx < events.length - 1 && <span className="timeline-connector" />}
          </button>
        ))}
      </div>
    </section>
  )
}
