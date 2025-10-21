import React, { useState, useRef, useEffect } from 'react'

type Message = { role: 'user' | 'assistant'; text: string }

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  // default to using ChatGPT flow; checkbox will opt into plain "translate" behavior
  const [useOpenAI, setUseOpenAI] = useState(true)
  const listRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // scroll to bottom on new message
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [messages, loading])

  async function send() {
    const text = input.trim()
    if (!text) return
    const userMsg: Message = { role: 'user', text }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      // Choose endpoint & payload depending on toggle
      const endpoint = useOpenAI ? '/openai_slang' : '/slang'
      const payload = useOpenAI ? { prompt: text } : { text }
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      // Normalize assistant text: prefer converted when present
      const assistantText = data.converted ?? data.original ?? data.converted_text ?? String(data)
      const assistantMsg: Message = { role: 'assistant', text: assistantText }
      setMessages((m) => [...m, assistantMsg])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: `Error contacting backend: ${err}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="chat-root">
      <div className="message-list" ref={listRef} aria-live="polite">
        {messages.length === 0 && <div className="empty">Type any jawn into the chat and PhillyGPT will give you a Kenzo response.</div>}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.role === 'assistant' && (
              <div className="assistant-art">
                <img src="/assets/assistant.png" alt="assistant" />
              </div>
            )}
            <div className="bubble">
              <div className="role">{m.role === 'user' ? 'You' : 'Assistant'}</div>
              <div className="text">{m.text}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="bubble">
              <div className="role">Assistant</div>
              <div className="text">Thinking…</div>
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type anything and I'll answer you with a Philly Attitude!"
          aria-label="Message"
        />
        <button onClick={send} disabled={loading || input.trim() === ''} aria-label="Send">
          Send
        </button>
        <div className="toggle-row">
          <label>
            <input
              type="checkbox"
              // checked=true means user requested plain translation; invert binding so
              // the default (unchecked) is the ChatGPT flow
              checked={!useOpenAI}
              onChange={(e) => setUseOpenAI(!e.target.checked)}
              aria-label="Translate me"
            />
            Translate me
          </label>
        </div>
      </div>
    </div>
  )
}
