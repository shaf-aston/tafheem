import { useEffect } from 'react'

import { useWheelX } from '../../lib/quran/useWheelX'

/**
 * Every ayah's number in one sideways strip, to jump straight to one. It
 * follows the reading: the ayah at the top of the list is marked and kept in
 * view, and the one being studied wears the accent. One stop for Tab, the
 * arrows walk it, so a long surah is not 286 presses to get past.
 */
export default function AyahRail({ count, here, open, onPick }) {
  const rail = useWheelX()
  useEffect(() => {
    const strip = rail.current
    const chip = strip?.children[here - 1]
    if (chip) strip.scrollTo({ left: chip.offsetLeft - (strip.clientWidth - chip.offsetWidth) / 2 })
  }, [rail, here])
  // Right is the next number, as the strip reads left to right.
  const walk = (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key]
    const n = Number(e.target.textContent) + (step ?? 0)
    if (step && n >= 1 && n <= count) rail.current.children[n - 1].focus()
  }

  return (
    <nav aria-label="Ayat" className="border-b border-[var(--border)]">
      <div ref={rail} onKeyDown={walk} className="strip-x relative gap-1 px-3 py-2">
        {Array.from({ length: count }, (_, i) => {
          const n = i + 1
          return (
            <button
              key={n}
              type="button"
              onClick={() => onPick(n)}
              tabIndex={n === here ? 0 : -1}
              aria-current={n === here ? 'location' : undefined}
              aria-label={n === open ? `${n}, being studied` : undefined}
              className={`press tap shrink-0 min-w-9 px-2 py-1 rounded-full type-small tabular-nums transition-colors
                ${n === open ? 'text-[var(--bg)] bg-[var(--c)]'
                  : n === here ? 'text-[var(--text)] bg-[var(--surface-hi)]'
                    : 'text-[var(--text-faint)] hover:text-[var(--text)]'}`}
            >
              {n}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
