/**
 * Starred, Narrators and Scholars behind one round button beside the search's
 * mic, so on a phone the books are not pushed down by a row of chips. The
 * button wears the More mark the bottom bar uses; it is tinted while one of
 * the three is open, so the reader can see where they are.
 *
 * Shuts on a pick, a click elsewhere or Escape (which hands focus back).
 */
import { useEffect, useId, useRef, useState } from 'react'

import MoreIcon from '../ui/MoreIcon'

export default function HadithMoreMenu({ items, accent }) {
  const [open, setOpen] = useState(false)
  const box = useRef(null)
  const button = useRef(null)
  const id = useId()
  const on = items.some((item) => item.on)

  useEffect(() => {
    if (!open) return undefined
    const outside = (event) => { if (!box.current?.contains(event.target)) setOpen(false) }
    const escape = (event) => {
      if (event.key !== 'Escape') return
      setOpen(false)
      button.current?.focus()
    }
    document.addEventListener('pointerdown', outside)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('pointerdown', outside)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  return (
    <div ref={box} className="relative shrink-0" style={{ '--c': accent }}>
      <button
        ref={button}
        type="button"
        aria-label="Starred, narrators and scholars"
        title="Starred, narrators and scholars"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((was) => !was)}
        className={`press w-10 h-10 grid place-items-center rounded-full border transition-colors ${
          on || open
            ? 'border-[var(--c)] text-[var(--c)]'
            : 'border-[var(--border)] text-[var(--text-faint)] hover:text-[var(--text)] hover:border-[var(--text-faint)]'
        }`}
      >
        <MoreIcon size={20} />
      </button>
      {open && (
        <div
          id={id}
          className="absolute end-0 top-full mt-2 z-[var(--layer-popover)] w-56 p-1.5 flex flex-col rounded-[var(--radius-md)]
            bg-[var(--surface-hi)] border border-[var(--border-hi)] shadow-[var(--shadow-pop)]"
        >
          {items.map(({ label, count, on: picked, pick }) => (
            <button
              key={label}
              type="button"
              aria-pressed={picked}
              onClick={() => { setOpen(false); pick() }}
              className={`press tap min-h-11 px-3 flex items-center justify-between gap-3 rounded-[var(--radius-sm)] type-body text-start transition-colors ${
                picked ? 'text-[var(--c)] bg-[var(--surface)]' : 'text-[var(--text)] hover:bg-[var(--surface)]'
              }`}
            >
              {label}
              {count > 0 && <span className="type-small text-[var(--text-faint)] tabular-nums">{count}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
