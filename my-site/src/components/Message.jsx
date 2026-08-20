import { motion } from 'motion/react'
import { renderMarkdown, escapeHtml } from '../lib/markdown.js'
import { relevancePct } from '../lib/api.js'

export default function Message({ msg }) {
  const isUser = msg.role === 'user'
  const bodyHtml = msg.error
    ? `<span class="err">${escapeHtml(msg.error)}</span>`
    : msg.text
      ? renderMarkdown(msg.text)
      : '<span class="thinking">thinking…</span>'

  return (
    <motion.article
      className={`msg glass${isUser ? ' user' : ''}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 240, damping: 24 }}
    >
      <div className="msg-head">
        <span className="msg-role">{isUser ? '🧑 You' : '📄 DocuMind'}</span>
        <span className="msg-time">{msg.time}</span>
      </div>
      <div className="msg-body" dangerouslySetInnerHTML={{ __html: bodyHtml }} />
      {msg.sources && msg.sources.length > 0 && (
        <details className="sources" open>
          <summary>Sources</summary>
          <ol>
            {msg.sources.map((s, i) => {
              const pct = relevancePct(s.score)
              const page = typeof s.page === 'number' ? ` · p.${s.page + 1}` : ''
              const snip = s.snippet ? s.snippet.slice(0, 280) + (s.snippet.length > 280 ? '…' : '') : ''
              return (
                <li key={i}>
                  <span className="src-head">{s.source || 'unknown'}{page}</span>
                  {pct != null && <span className="src-rel">{pct}% match</span>}
                  {snip && <span className="src-snippet">{snip}</span>}
                </li>
              )
            })}
          </ol>
        </details>
      )}
    </motion.article>
  )
}
