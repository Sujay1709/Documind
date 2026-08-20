import { useEffect, useRef } from 'react'
import Message from './Message.jsx'

export default function Chat({ messages }) {
  const endRef = useRef(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [messages])

  return (
    <section className="thread">
      {messages.map((m) => (
        <Message key={m.id} msg={m} />
      ))}
      <div ref={endRef} />
    </section>
  )
}
