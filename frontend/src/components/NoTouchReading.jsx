/**
 * Reading the Qur'an on a phone without touching its words: for someone
 * without wudu, or during menstruation. On, the ayahs neither scroll nor open
 * under a finger, and a strip down the edge, holding no text, scrolls them.
 *
 * Only on a touch screen. A mouse never touches the words, so nothing changes
 * there.
 */
import { useEffect, useRef, useState } from 'react'

// Long enough that a tap never reads as a hold.
const HOLD_MS = 450
const HINT_MS = 4000
const SAY = 'Scroll by the side strip only, so your finger never touches the Qur\'an\'s words. '
  + 'For reading without wudu, or during menstruation.'

/** The switch in the reader's bar. Held, it says what it is. */
export function NoTouchButton({ on, onChange }) {
  const [hint, setHint] = useState(false)
  const hold = useRef(null)
  const held = useRef(false)

  useEffect(() => {
    if (!hint) return undefined
    const timer = setTimeout(() => setHint(false), HINT_MS)
    return () => clearTimeout(timer)
  }, [hint])
  useEffect(() => () => clearTimeout(hold.current), [])

  const press = () => {
    held.current = false
    hold.current = setTimeout(() => { held.current = true; setHint(true) }, HOLD_MS)
  }
  const lift = () => clearTimeout(hold.current)

  return (
    <>
      <button
        type="button"
        aria-pressed={on}
        aria-label="Reading without wudu"
        aria-description={SAY}
        onPointerDown={press}
        onPointerUp={lift}
        onPointerLeave={lift}
        onPointerCancel={lift}
        // A hold is for the hint, not the switch; nor is it the phone's own menu.
        onClick={() => (held.current ? (held.current = false) : onChange(!on))}
        onContextMenu={(e) => e.preventDefault()}
        className={`press tap select-none grid place-items-center w-[var(--layout-chip)] h-[var(--layout-chip)] rounded-full border transition-colors
          ${on ? 'text-[var(--bg)] bg-[var(--c)] border-[var(--c)]' : 'text-[var(--text-faint)] border-[var(--border)]'}`}
      >
        {/* A pointing hand, struck through. */}
        <svg aria-hidden="true" viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 4.5V4a2 2 0 0 0-2.41-1.96" />
          <path d="M13.9 8.4a2 2 0 0 0-1.26-1.3" />
          <path d="M21.7 16.2A8 8 0 0 0 22 14v-3a2 2 0 1 0-4 0v-1a2 2 0 0 0-3.63-1.16" />
          <path d="m7 15-1.8-1.8a2 2 0 0 0-2.79 2.86L6 19.7a7.74 7.74 0 0 0 6 2.3h2a8 8 0 0 0 5.66-2.34" />
          <path d="M6 6v8" />
          <path d="m2 2 20 20" />
        </svg>
      </button>
      {hint && (
        <p
          role="status"
          className="pointer-events-none fade-in fixed inset-x-4 top-1/3 mx-auto z-[var(--layer-popover)] max-w-xs p-3
            rounded-[var(--radius-md)] bg-[var(--surface-hi)] border border-[var(--border-hi)] shadow-[var(--shadow-pop)]
            type-small text-[var(--text)] leading-snug"
        >
          {SAY}
        </p>
      )}
    </>
  )
}

// How fast a flick slows, per millisecond, and when it has stopped.
const DRAG = 0.996
const STILL = 0.02

/**
 * The strip that scrolls `list` while its words are not to be touched: drag
 * it as you would the page, flick it and it carries on. `on` slides it in from
 * the edge and back out again, the same step sideways the pages take.
 */
export function ScrollPad({ list, on }) {
  // Still drawn while it slides out; gone once that is over.
  const [shown, setShown] = useState(on)
  if (on && !shown) setShown(true)
  const last = useRef(null)
  const speed = useRef(0)
  const coast = useRef(0)
  useEffect(() => () => cancelAnimationFrame(coast.current), [])

  const down = (e) => {
    cancelAnimationFrame(coast.current)
    e.currentTarget.setPointerCapture(e.pointerId)
    last.current = { y: e.clientY, t: e.timeStamp }
    speed.current = 0
  }
  const move = (e) => {
    if (!last.current || !list.current) return
    const dy = e.clientY - last.current.y
    const dt = Math.max(1, e.timeStamp - last.current.t)
    list.current.scrollBy(0, -dy)
    speed.current = dy / dt
    last.current = { y: e.clientY, t: e.timeStamp }
  }
  const up = () => {
    last.current = null
    let then = performance.now()
    const glide = (now) => {
      const dt = now - then
      then = now
      speed.current *= DRAG ** dt
      if (Math.abs(speed.current) < STILL || !list.current) return
      list.current.scrollBy(0, -speed.current * dt)
      coast.current = requestAnimationFrame(glide)
    }
    coast.current = requestAnimationFrame(glide)
  }

  if (!shown) return null
  return (
    <div
      aria-hidden="true"
      onAnimationEnd={() => !on && setShown(false)}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerCancel={up}
      className={`${on ? 'slide-prev' : 'slide-away'} touch-none select-none w-11 shrink-0 grid place-items-center border-l border-[var(--border)] bg-[var(--surface-hi)] text-[var(--text-faint)]`}
      style={{ '--slide-from': '100%' }}
    >
      <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m7 9 5-5 5 5M7 15l5 5 5-5" />
      </svg>
    </div>
  )
}
