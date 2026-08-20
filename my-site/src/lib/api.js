// DocuMind API client — talks to the FastAPI/Ollama backend.
// Dev: Vite proxies these paths to :8000 (see vite.config.js).
// Prod: serve the built app from the same origin as the API.

// Optional admin token (only needed when DOCUMIND_API_TOKEN is set server-side).
const TOKEN_KEY = 'documind:token'
export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}
export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}
function authHeaders() {
  const t = getToken()
  return t ? { 'X-Documind-Token': t } : {}
}

export async function fetchSources() {
  try {
    const r = await fetch('/api/sources', { headers: authHeaders() })
    if (!r.ok) return []
    const data = await r.json()
    return data.sources || []
  } catch {
    return []
  }
}

export async function uploadFiles(files) {
  const fd = new FormData()
  for (const f of files) fd.append('files', f)
  const r = await fetch('/upload', { method: 'POST', body: fd, headers: authHeaders() })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.error || `Upload failed (HTTP ${r.status})`)
  return data.processed || []
}

export async function indexByPath(path) {
  const r = await fetch('/api/upload-by-path', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ path }),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`)
  return data.processed || []
}

/**
 * Stream a grounded answer over Server-Sent Events.
 * The backend emits `data: {json}\n\n` frames of type "sources" | "token" | "error".
 * Callbacks: onSources(list), onToken(text), onError(message).
 * Returns when the stream ends. Pass an AbortSignal to cancel.
 */
export async function streamChat({ question, source, history = [], onSources, onToken, onError, signal }) {
  const r = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ question, source: source || null, history }),
    signal,
  })
  if (!r.ok || !r.body) {
    const err = await r.json().catch(() => ({ error: `HTTP ${r.status}` }))
    onError?.(err.error || 'Request failed')
    return
  }
  const reader = r.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const frame = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      const line = frame.split('\n').find((l) => l.startsWith('data: '))
      if (!line) continue
      let payload
      try {
        payload = JSON.parse(line.slice(6))
      } catch {
        continue
      }
      if (payload.type === 'sources') onSources?.(payload.sources || [])
      else if (payload.type === 'token') onToken?.(payload.text || '')
      else if (payload.type === 'error') onError?.(payload.message || 'Unknown error')
    }
  }
}

// Relevance % from a re-rank logit, matching the vanilla UI's display.
export function relevancePct(score) {
  if (score == null) return null
  return Math.round(100 / (1 + Math.exp(-score)))
}
