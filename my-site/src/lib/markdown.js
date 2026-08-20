// Tiny, safe markdown -> HTML renderer (no eval, escapes first).
// Ported from the vanilla DocuMind SPA so streamed answers render the same.
export function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// Private-use sentinels: they never occur in normal document text and survive
// HTML-escaping, so fenced code blocks can be stashed then restored intact.
const S_OPEN = ''
const S_CLOSE = ''

export function renderMarkdown(text) {
  const fenced = []
  text = String(text).replace(/```(\w+)?\n([\s\S]*?)```/g, (_m, _l, code) => {
    const i = fenced.push(`<pre><code>${escapeHtml(code)}</code></pre>`) - 1
    return `${S_OPEN}${i}${S_CLOSE}`
  })
  text = escapeHtml(text)
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
  text = text.replace(/\n{2,}/g, '</p><p>')
  text = `<p>${text.replace(/\n/g, '<br>')}</p>`
  text = text.replace(new RegExp(`${S_OPEN}(\\d+)${S_CLOSE}`, 'g'), (_, i) => fenced[Number(i)])
  return text
}
