/** Copy some text to the clipboard, flipping to a checked "Copied" state for
 * a moment. Moved out of IraabAnalyzer so any panel with a copy action reuses
 * it instead of growing its own timeout/flag pair. */
import { useCallback, useEffect, useRef, useState } from 'react'

export const COPY_RESET_MS = 2000

export default function CopyButton({ text, label = 'Copy analysis', small = false }) {
  const [copied, setCopied] = useState(false)
  const timeoutRef = useRef(null)

  useEffect(() => () => window.clearTimeout(timeoutRef.current), [])

  const onCopy = useCallback(() => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        setCopied(true)
        window.clearTimeout(timeoutRef.current)
        timeoutRef.current = window.setTimeout(() => setCopied(false), COPY_RESET_MS)
      })
      .catch(() => setCopied(false))
  }, [text])

  return (
    <button
      type="button"
      onClick={onCopy}
      className={`press tap shrink-0 border transition-colors ${
        small ? 'px-2 py-0.5 type-tiny rounded-full' : 'px-3 py-2 text-xs rounded-[var(--radius-md)]'
      }`}
      style={{
        borderColor: copied ? 'var(--success)' : 'var(--border)',
        color: copied ? 'var(--success)' : 'var(--text-dim)',
      }}
    >
      {copied ? '✓ Copied' : label}
    </button>
  )
}
