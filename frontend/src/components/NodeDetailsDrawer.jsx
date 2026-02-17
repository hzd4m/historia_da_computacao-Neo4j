export default function NodeDetailsDrawer({ node, onClose }) {
  if (!node) return null

  const fields = [
    { label: 'Ano', value: node.year },
    { label: 'Descrição', value: node.description },
    { label: 'Bio', value: node.bio },
    { label: 'Impacto', value: node.impacto },
    { label: 'Problema resolvido', value: node.problema_resolvido },
    { label: 'Nacionalidade', value: node.nacionalidade },
    { label: 'Contribuição-chave', value: node.contribuicao_chave },
    { label: 'Tipo', value: node.tipo },
    { label: 'Material', value: node.material },
    { label: 'Paper', value: node.paper },
    { label: 'Tecnologia base', value: node.tecnologia_base },
    { label: 'Fonte', value: node.fonte },
  ]

  return (
    <aside className="details-drawer" role="dialog" aria-label="Detalhes do nó">
      <button className="drawer-close" onClick={onClose}>
        Fechar
      </button>

      <h2>{node.name}</h2>
      <p className={`node-chip node-chip-${(node.category || '').toLowerCase()}`}>{node.category}</p>

      <div className="drawer-fields">
        {fields.map(
          (f) =>
            f.value != null &&
            f.value !== '' &&
            f.value !== 'Sem descrição disponível.' && (
              <p key={f.label}>
                <strong>{f.label}:</strong> {String(f.value)}
              </p>
            )
        )}
      </div>

      {node.uid && (
        <p className="muted drawer-uid">UID: {node.uid}</p>
      )}

      <div className="drawer-sources">
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
