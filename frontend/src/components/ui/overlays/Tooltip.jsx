import { useState } from 'react'

/**
 * Floating explanation above an inline element. Hover and keyboard focus both
 * open it (the wrapper takes focus, so a name with an explanation is reached by
 * Tab), and the native `title` keeps it reachable on touch and by a screen
 * reader. The bubble's text is drawn from data-tip by CSS so it is never copied.
 * `below` hangs the bubble under the element instead, where a box clips above it
 * (the tarkeeb chart's first row of names sits right under its words).
 */
export default function Tooltip({ text, children, below = false }) {
  const [visible, setVisible] = useState(false)
  if (!text) return children

  return (
    <span
      className="relative inline-flex items-center"
      tabIndex={0}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      title={text}
    >
      {children}
      {/* w-max: the bubble is as wide as its text, never squeezed to its parent's
          column (a chart name is capped at 6.5em), then wrapped at the cap below */}
      <span
        aria-hidden="true"
        data-tip={text}
        className={`tip-bubble pointer-events-none absolute left-1/2 -translate-x-1/2 z-[var(--layer-tip)]
          ${below ? 'top-full mt-2' : 'bottom-full mb-2'}
          px-2.5 py-1.5 rounded-[var(--radius-sm)] shadow-xl
          bg-[var(--surface-hi)] border border-[var(--border-hi)]
          text-[var(--text)] type-label leading-snug whitespace-normal w-max max-w-[min(240px,80vw)] text-center
          transition-opacity duration-[calc(var(--motion-instant-ms)*1ms)] ${visible ? 'opacity-100' : 'opacity-0'}`}
      />
    </span>
  )
}
