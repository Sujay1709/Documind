import { useRef } from 'react'
import { AnimatePresence, motion } from 'motion/react'

export default function Composer({ activeSource, onClearSource, onSend, busy }) {
  const taRef = useRef(null)

  function submit(e) {
    e?.preventDefault()
    const val = taRef.current?.value.trim()
    if (!val || busy) return
    onSend(val)
    if (taRef.current) {
      taRef.current.value = ''
      taRef.current.style.height = 'auto'
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function autogrow(e) {
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 180) + 'px'
  }

  return (
    <footer className="composer">
      <AnimatePresence>
        {activeSource && (
          <motion.div
            className="source-pill glass"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
          >
            <span>📄 <b>{activeSource}</b></span>
            <button type="button" title="Ask across all docs" aria-label="Ask across all documents" onClick={onClearSource}>✕</button>
          </motion.div>
        )}
      </AnimatePresence>

      <form className="ask glass" onSubmit={submit}>
        <textarea
          ref={taRef}
          rows={1}
          placeholder="Ask anything about your documents…"
          onKeyDown={onKeyDown}
          onInput={autogrow}
        />
        <motion.button
          className="send"
          type="submit"
          disabled={busy}
          whileHover={{ scale: busy ? 1 : 1.06 }}
          whileTap={{ scale: 0.94 }}
          title="Send (Enter)"
          aria-label={busy ? 'Sending question' : 'Send question'}
        >
          ➤
        </motion.button>
      </form>

      <div className="foot">
        <span>nomic-embed · ms-marco re-ranker · Ollama nemotron-mini</span>
        <a href="https://github.com/Sujay1709/documind-rag" target="_blank" rel="noreferrer">Source &amp; docs ↗</a>
      </div>
    </footer>
  )
}
