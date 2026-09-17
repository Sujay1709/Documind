import { useRef, useState } from 'react'
import { motion } from 'motion/react'

const SUGGESTIONS = [
  'Summarize this document in a few sentences.',
  'What are the key points?',
  'List the main sections.',
  'What conclusions does it reach?',
]

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
}
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200, damping: 22 } },
}

export default function Hero({ status, onFiles, onSuggest, disabledSuggest, uploading }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)

  function handleDrop(e) {
    e.preventDefault()
    setDrag(false)
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type === 'application/pdf' || /\.pdf$/i.test(f.name))
    if (files.length) onFiles(files)
  }

  return (
    <motion.section className="hero" variants={container} initial="hidden" animate="show">
      <motion.div className="badge" variants={item}>🔒 Private document context · Ollama-compatible inference</motion.div>
      <motion.h1 variants={item}>Drop a PDF to start</motion.h1>
      <motion.p variants={item}>
        DocuMind indexes your PDF into a persistent Chroma store, retrieves and re-ranks the best
        chunks, then streams an evidence-grounded answer from your configured Ollama-compatible model.
      </motion.p>

      <motion.div
        className={`upload glass${drag ? ' drag' : ''}`}
        variants={item}
        whileHover={{ y: -4 }}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
      >
        <motion.div className="icon" animate={{ y: [0, -5, 0] }} transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}>
          ⤵
        </motion.div>
        <button className="btn-primary" type="button" disabled={uploading} onClick={() => inputRef.current?.click()}>
          {uploading ? 'Indexing…' : 'Choose PDF'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          hidden
          multiple
          disabled={uploading}
          onChange={(e) => {
            const files = Array.from(e.target.files || [])
            if (files.length) onFiles(files)
            e.target.value = ''
          }}
        />
        <div className="status" role="status" aria-live="polite">{status}</div>
        <div className="hint">Up to 500 MB. Embeddings and chat run through the configured DocuMind server.</div>
      </motion.div>

      <motion.h2 className="suggest-label" variants={item}>Or try one of these</motion.h2>
      <motion.div className="suggest" variants={item}>
        {SUGGESTIONS.map((q) => (
          <motion.button
            key={q}
            type="button"
            className="chip"
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.97 }}
            disabled={disabledSuggest}
            onClick={() => onSuggest(q)}
          >
            {q}
          </motion.button>
        ))}
      </motion.div>
    </motion.section>
  )
}
