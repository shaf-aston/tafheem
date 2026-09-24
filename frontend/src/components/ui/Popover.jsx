/**
 * A pill that opens a small floating panel. For settings chosen once and left:
 * they stay one click away without taking room on a line that needs it.
 *
 * Shuts on a click elsewhere or Escape, and Escape hands focus back to the
 * pill. Not Disclosure: a <details> pushes its content into the page, and
 * inside a wrapping row that reflows the row, which is the thing this avoids.
 */
import { useEffect, useId, useRef, useState } from 'react'

export default function Popover({ label, title, children }) {
  const [open, setOpen] = useState(false)
  const box = useRef(null)
  const pill = useRef(null)
  const id = useId()

  useEffect(() => {
    if (!open) return undefined
    const outside = (event) => { if (!box.current?.contains(event.target)) setOpen(false) }
    const escape = (event) => {
      if (event.key !== 'Escape') return
      setOpen(false)
      pill.current?.focus()
    }
    document.addEventListener('pointerdown', outside)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('pointerdown', outside)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  return (
    <div ref={box} className="relative">
      {/* Same height and text size as a Segmented row, the control it sits beside. */}
      <button
        ref={pill}
        type="button"
        title={title}
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((was) => !was)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
          bg-[var(--surface)] border border-[var(--border)] text-[var(--text-dim)]
          hover:text-[var(--text)] hover:border-[var(--border-hi)] transition-colors"
      >
        {label}
        <svg
          aria-hidden="true" viewBox="0 0 24 24" width="10" height="10" fill="none"
          stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
          className={`transition-transform ${open ? 'rotate-180' : ''}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {/* w-max: an absolute box otherwise shrinks to the pill's width and
          breaks every caption and choice inside it onto two lines. */}
      {open && (
        <div
          id={id}
          className="absolute end-0 top-full mt-2 z-30 w-max p-3 rounded-[var(--radius-md)]
            bg-[var(--surface-hi)] border border-[var(--border-hi)] shadow-[var(--shadow-pop)]"
        >
          {children}
        </div>
      )}
    </div>
  )
}
