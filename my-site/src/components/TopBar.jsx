import { motion } from 'motion/react'

export default function TopBar({
  theme,
  onToggleTheme,
  docCount,
  docs,
  activeSource,
  onSelectSource,
  docsLoading,
  docsError,
  hasToken,
  onAdmin,
  onAbout,
  onReset,
}) {
  return (
    <motion.header
      className="bar glass"
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 220, damping: 26 }}
    >
      <motion.div className="logo" whileHover={{ rotate: -8, scale: 1.06 }}>📄</motion.div>
      <div className="name">DocuMind</div>
      <div className="tag">· grounded RAG · Ollama-compatible inference</div>
      <div className="spacer" />
      <div className="pill docs" title="Indexed documents on this server">
        📚 <b>{docCount}</b> docs
      </div>
      {docs.length > 0 && (
        <label className="doc-select">
          <span className="sr-only">Search scope</span>
          <select
            value={activeSource || ''}
            onChange={(e) => onSelectSource(e.target.value || null)}
            aria-label="Choose a document to search"
          >
            <option value="">All documents</option>
            {docs.map((doc) => <option key={doc} value={doc}>{doc}</option>)}
          </select>
        </label>
      )}
      {docsLoading && <span className="status-inline">Loading…</span>}
      {docsError && <span className="status-inline error-inline" role="status">Server unavailable</span>}
      <button className="btn-ghost" type="button" onClick={onAbout}>About</button>
      {hasToken && <button className="btn-ghost danger" type="button" onClick={onReset}>Reset data</button>}
      <button className="btn-ghost" type="button" onClick={onAdmin}>
        {hasToken ? 'Sign out' : 'Admin'}
      </button>
      <button className="btn-ghost" type="button" onClick={onToggleTheme} title="Toggle theme" aria-label="Toggle color theme">
        {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
      </button>
    </motion.header>
  )
}
