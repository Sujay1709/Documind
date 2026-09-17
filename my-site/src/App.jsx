import { useCallback, useEffect, useRef, useState } from 'react'
import TopBar from './components/TopBar.jsx'
import Hero from './components/Hero.jsx'
import Chat from './components/Chat.jsx'
import Composer from './components/Composer.jsx'
import { fetchSources, uploadFiles, streamChat, getToken, setToken } from './lib/api.js'

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('documind:theme') || 'dark')
  const [docs, setDocs] = useState([])
  const [docsLoading, setDocsLoading] = useState(true)
  const [docsError, setDocsError] = useState('')
  const [activeSource, setActiveSource] = useState(null)
  const [messages, setMessages] = useState([])
  const [started, setStarted] = useState(false)
  const [busy, setBusy] = useState(false)
  const [hasToken, setHasToken] = useState(!!getToken())
  const [uploadStatus, setUploadStatus] = useState('No file selected.')
  const [uploading, setUploading] = useState(false)
  const idc = useRef(0)
  const nextId = () => `m${++idc.current}`

  // Theme -> <html> class + persistence.
  useEffect(() => {
    const el = document.documentElement
    el.classList.remove('light', 'dark')
    el.classList.add(theme)
    localStorage.setItem('documind:theme', theme)
  }, [theme])

  const refreshDocs = useCallback(async () => {
    setDocsLoading(true)
    try {
      setDocs(await fetchSources())
      setDocsError('')
    } catch (e) {
      setDocsError(String(e.message || e))
    } finally {
      setDocsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshDocs()
    const t = setInterval(refreshDocs, 30000)
    return () => clearInterval(t)
  }, [refreshDocs])

  const handleFiles = useCallback(
    async (files) => {
      if (uploading) return
      setUploading(true)
      setUploadStatus(`Uploading ${files.map((f) => f.name).join(', ')}…`)
      try {
        const processed = await uploadFiles(files)
        const names = processed.map((x) => x.source).join(', ')
        setUploadStatus(`Indexed ${names}`)
        setStarted(true)
        if (processed[0]?.source) setActiveSource(processed[0].source)
        await refreshDocs()
      } catch (e) {
        setUploadStatus(String(e.message || e))
      } finally {
        setUploading(false)
      }
    },
    [refreshDocs, uploading],
  )

  const sendQuestion = useCallback(
    async (q) => {
      if (busy) return
      if (docs.length === 0) {
        setStarted(true)
        setMessages((prev) => [
          ...prev,
          { id: nextId(), role: 'bot', text: '', error: 'Upload a PDF first, then ask. Everything runs locally through your DocuMind server + Ollama.', time: now() },
        ])
        return
      }
      setStarted(true)
      setBusy(true)
      const botId = nextId()
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: 'user', text: q, time: now() },
        { id: botId, role: 'bot', text: '', sources: [], time: now() },
      ])

      let acc = ''
      try {
        await streamChat({
          question: q,
          source: activeSource,
          history: [],
          onSources: (list) => setMessages((prev) => prev.map((m) => (m.id === botId ? { ...m, sources: list } : m))),
          onToken: (tok) => {
            acc += tok
            setMessages((prev) => prev.map((m) => (m.id === botId ? { ...m, text: acc } : m)))
          },
          onError: (msg) => setMessages((prev) => prev.map((m) => (m.id === botId ? { ...m, error: msg } : m))),
        })
      } catch (e) {
        setMessages((prev) => prev.map((m) => (m.id === botId ? { ...m, error: String(e.message || e) } : m)))
      } finally {
        setBusy(false)
      }
    },
    [busy, docs.length, activeSource],
  )

  function toggleTheme() {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'))
  }

  function handleAdmin() {
    if (hasToken) {
      setToken('')
      setHasToken(false)
      return
    }
    const t = prompt('Paste your DocuMind admin token (X-Documind-Token). Only needed when DOCUMIND_API_TOKEN is set on the server. Leave blank to cancel.')
    if (t && t.trim()) {
      setToken(t.trim())
      setHasToken(true)
    }
  }

  // Drag a PDF anywhere to index it, even mid-conversation.
  function onDrop(e) {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type === 'application/pdf' || /\.pdf$/i.test(f.name))
    if (files.length) handleFiles(files)
  }

  return (
    <div className="root-wrap" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <div className="ambient" aria-hidden="true">
        <div className="ambient-grid" />
        <div className="ambient-orbit" />
      </div>
      <div className="app">
        <TopBar
          theme={theme}
          onToggleTheme={toggleTheme}
          docCount={docs.length}
          docs={docs}
          activeSource={activeSource}
          onSelectSource={setActiveSource}
          docsLoading={docsLoading}
          docsError={docsError}
          hasToken={hasToken}
          onAdmin={handleAdmin}
        />
        <main className="main">
          {started ? (
            <Chat messages={messages} />
          ) : (
            <Hero
              status={uploadStatus}
              onFiles={handleFiles}
              onSuggest={sendQuestion}
              disabledSuggest={busy || uploading || Boolean(docsError)}
              uploading={uploading}
            />
          )}
        </main>
        <Composer
          activeSource={activeSource}
          onClearSource={() => setActiveSource(null)}
          onSend={sendQuestion}
          busy={busy || uploading || Boolean(docsError)}
        />
      </div>
    </div>
  )
}
