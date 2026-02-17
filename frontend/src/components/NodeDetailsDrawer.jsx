export default function NodeDetailsDrawer({ node, onClose }) {
  if (!node) return null

  return (
    <aside className="details-drawer" role="dialog" aria-label="Detalhes do nó">
      <button className="drawer-close" onClick={onClose}>
        Fechar
      </button>

      <h2>{node.name}</h2>
      <p className="node-chip">{node.category}</p>
      <p>
        <strong>Ano:</strong> {node.year ?? 'N/D'}
      </p>
      <p>
        <strong>Descrição:</strong> {node.description}
      </p>

      <div>
        <strong>Fontes citadas:</strong>
        {Array.isArray(node.sourceLinks) && node.sourceLinks.length > 0 ? (
          <ul className="source-list">
            {node.sourceLinks.map((src) => (
              <li key={src}>
                <a href={src} target="_blank" rel="noreferrer">
                  {src}
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Sem fontes estruturadas neste nó.</p>
        )}
      </div>
    </aside>
  )
}
