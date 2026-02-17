const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

function parseJsonSafe(text) {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const raw = await response.text()
  const json = parseJsonSafe(raw)

  if (!response.ok) {
    const detail = (json && (json.detail || json.error)) || raw || 'Erro desconhecido na API'
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return json ?? {}
}

export async function searchHybrid(query) {
  return request('/search', {
    method: 'POST',
    body: JSON.stringify({ query })
  })
}

export async function fetchGraph(uid) {
  return request(`/graph/${encodeURIComponent(uid)}`)
}

export { API_BASE_URL }
