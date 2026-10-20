/**
 * One field that opens a fast-scrolling list to pick from: Surah, Ayah, Juz,
 * or anything else that is "one of these N things" rather than free text.
 *
 * Replaces typing a number into a box and pressing a separate submit button.
 * Open, type a letter or two to narrow the list, press the one row left or
 * Enter: two actions instead of five. The list itself scrolls like a wheel —
 * each row fades and shrinks toward the top and bottom edges via a
 * scroll-driven CSS animation (view-timeline), so the row under the pointer
 * always reads as "the one about to be picked" without any JS scroll math.
 * Browsers without view-timeline (Firefox, Safari < 18) just show a plain
 * list; nothing breaks, the animation is a `@supports` bonus.
 *
 * Pure UI: options are `{ value, label, sub? }`; the caller owns what a pick
 * means. One component so Surah, Ayah and Juz can never drift into three
 * different pickers with three different feels.
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react'

export default function WheelSelect({ label, value, options, onChange, accent, placeholder = 'Type to search…' }) {
  const [open, setOpen] = useState(false)
  const [typed, setTyped] = useState('')
  const [active, setActive] = useState(0)
  const box = useRef(null)
  const input = useRef(null)
  const listId = useId()

  const current = options.find((o) => o.value === value) ?? null

  const listed = useMemo(() => {
    const needle = typed.trim().toLowerCase()
    if (!needle) return options
    return options.filter(
      (o) => o.label.toLowerCase().includes(needle) || String(o.value).includes(needle),
    )
  }, [options, typed])

  // Clamped rather than reset via an effect: `active` only ever needs to stay
  // in range as the filtered list shrinks, never to jump on its own.
  const activeIndex = Math.min(active, Math.max(listed.length - 1, 0))

  useEffect(() => {
    if (!open) return undefined
    const outside = (e) => { if (!box.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])

  const pick = (opt) => {
    onChange(opt.value)
    setOpen(false)
    setTyped('')
  }

  const openList = () => {
    setOpen(true)
    // Focus moves after the input mounts, not before, or it opens the list
    // on top of a keyboard that has not appeared yet on phones.
    requestAnimationFrame(() => input.current?.focus())
  }

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive(Math.min(activeIndex + 1, listed.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(Math.max(activeIndex - 1, 0)) }
    else if (e.key === 'Enter') { e.preventDefault(); if (listed[activeIndex]) pick(listed[activeIndex]) }
    else if (e.key === 'Escape') { e.preventDefault(); setOpen(false) }
  }

  return (
    <div ref={box} className="relative flex-1">
      <label className="text-[var(--text-faint)] text-xs uppercase tracking-wide block mb-1">{label}</label>
      <button
        type="button"
        onClick={openList}
        aria-haspopup="listbox"
        aria-expanded={open}
        style={{ '--c': accent }}
        className="w-full text-start rounded-[var(--radius-md)] p-3 bg-[var(--surface)] text-[var(--text)]
          border border-[var(--border)] hover:border-[var(--border-hi)] focus:border-[var(--c)]
          focus:outline-none transition-colors flex items-center justify-between gap-2"
      >
        <span className={current ? '' : 'text-[var(--text-faint)]'}>
          {current ? current.label : placeholder}
        </span>
        <svg aria-hidden="true" viewBox="0 0 24 24" width="14" height="14" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}>
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute z-(--layer-popover) mt-1 w-full rounded-[var(--radius-md)] bg-[var(--surface-hi)]
            border border-[var(--border-hi)] shadow-[var(--shadow-pop)] overflow-hidden"
        >
          <input
            ref={input}
            type="text"
            value={typed}
            onChange={(e) => { setTyped(e.target.value); setActive(0) }}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            aria-controls={listId}
            aria-activedescendant={listed[activeIndex] ? `${listId}-${listed[activeIndex].value}` : undefined}
            className="w-full px-3 py-2 text-sm bg-transparent border-b border-[var(--border)]
              text-[var(--text)] placeholder:text-[var(--text-faint)] focus:outline-none"
          />
          <ul id={listId} role="listbox" className="wheel-list max-h-56 overflow-y-auto py-1">
            {listed.length === 0 ? (
              <li className="px-3 py-2 type-small text-[var(--text-faint)]">No match</li>
            ) : (
              listed.map((o, i) => (
                <li key={o.value} id={`${listId}-${o.value}`} role="option" aria-selected={o.value === value}>
                  <button
                    type="button"
                    onClick={() => pick(o)}
                    onMouseEnter={() => setActive(i)}
                    style={{ '--c': accent }}
                    className={`wheel-row w-full text-start px-3 py-1.5 flex items-baseline justify-between gap-3
                      transition-colors ${
                        i === activeIndex ? 'bg-[color-mix(in_srgb,var(--c)_14%,transparent)] text-[var(--c)]'
                          : o.value === value ? 'text-[var(--c)]' : 'text-[var(--text)]'
                      }`}
                  >
                    <span className="truncate">{o.label}</span>
                    {o.sub && <span className="type-small text-[var(--text-faint)] shrink-0">{o.sub}</span>}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
