import { motion } from 'motion/react'

const FEATURES = [
  ['Evidence first', 'Every answer leads with a verbatim quote and can abstain when the indexed context is not enough.'],
  ['Page-aware retrieval', 'Chunks keep page and section metadata so related evidence stays together during reranking.'],
  ['Built for inspection', 'Citations expose the source, page, section, and relevance score behind each response.'],
  ['Local by design', 'Run the full Python pipeline with Ollama and ChromaDB, or connect the service to an Ollama-compatible host.'],
]

export default function AboutPage({ onBack }) {
  return (
    <main className="main about-page">
      <motion.section
        className="about-hero"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <div className="badge">System brief · DocuMind</div>
        <h1>Understand the document, not the guess.</h1>
        <p>
          DocuMind is a document-grounded RAG workspace for asking better questions
          of PDFs. It retrieves evidence, reranks it, and shows you where an answer came from.
        </p>
        <button className="btn-primary" type="button" onClick={onBack}>Back to workspace</button>
      </motion.section>

      <section className="about-grid" aria-label="DocuMind features">
        {FEATURES.map(([title, text]) => (
          <article className="about-panel" key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>

      <section className="about-meta" aria-label="Project information">
        <div>
          <span className="meta-label">Owner</span>
          <strong>Sujay Gopal</strong>
          <a href="https://github.com/Sujay1709/Documind" target="_blank" rel="noreferrer">GitHub repository ↗</a>
        </div>
        <div>
          <span className="meta-label">License</span>
          <strong>MIT License</strong>
          <span>Free to inspect, adapt, and self-host.</span>
        </div>
        <div>
          <span className="meta-label">Runtime</span>
          <strong>Python · Ollama · ChromaDB</strong>
          <span>React/Vite interface with streamed answers.</span>
        </div>
      </section>
    </main>
  )
}
