import { useState } from 'react'

/**
 * Floating explanation above an inline element. Hover and keyboard focus both
 * open it, and the native `title` keeps it reachable on touch and names it to a
 * screen reader.
 *
 * The bubble draws its text from data-tip (index.css, .tip-bubble) instead of
 * holding it: text held inside the page is text a drag-select copies, and a
 * copied line of Arabic came out with the English notes of its words in it.
 */
export default function Tooltip({ text, children }) {
  const [visible, setVisible] = useState(false)
  if (!text) return children

  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      title={text}
    >
      {children}
      <span
        aria-hidden="true"
        data-tip={text}
        className={`tip-bubble pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50
          px-2.5 py-1.5 rounded-[var(--radius-sm)] shadow-xl
          bg-[var(--surface-hi)] border border-[var(--border-hi)]
          text-[var(--text)] text-xs leading-snug whitespace-normal max-w-[240px] text-center
          transition-opacity duration-[calc(var(--motion-instant-ms)*1ms)] ${visible ? 'opacity-100' : 'opacity-0'}`}
      />
    </span>
  )
}
