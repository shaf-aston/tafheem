import { useState } from 'react'

/**
 * Floating explanation above an inline element. Hover and keyboard focus both
 * open it, and the native `title` keeps it reachable on touch.
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
        role="tooltip"
        aria-hidden={!visible}
        className={`pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50
          px-2.5 py-1.5 rounded-[var(--radius-sm)] shadow-xl
          bg-[var(--surface-hi)] border border-[var(--border-hi)]
          text-[var(--text)] text-xs leading-snug whitespace-normal max-w-[240px] text-center
          transition-opacity duration-[calc(var(--motion-instant-ms)*1ms)] ${visible ? 'opacity-100' : 'opacity-0'}`}
      >
        {text}
      </span>
    </span>
  )
}
