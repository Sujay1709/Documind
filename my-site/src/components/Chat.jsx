import { useEffect, useRef } from 'react'
import Message from './Message.jsx'

export default function Chat({ messages, indexedDocs = [] }) {
  const endRef = useRef(null)
  useEffect(() => {
    const scroller = endRef.current?.closest('.main')
    if (scroller) {
      scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' })
    }
  }, [messages])

  return (
    <section className="thread" aria-live="polite" aria-label="Conversation">
      {indexedDocs.length > 0 && (
        <div className="indexed-notice" role="status">
          <strong>Ready to ask</strong>
          <span>{indexedDocs.map((doc) => `${doc.source} · ${doc.chunks} chunks`).join(' · ')}</span>
        </div>
      )}
      {messages.map((m) => (
        <Message key={m.id} msg={m} />
      ))}
      <div ref={endRef} />
    </section>
  )
}
