/**
 * The app's one dropdown: a pill that opens a small floating wheel of choices.
 * Spin it, or, on a long list, type and it spins there ("nis" or "4" lands on
 * An-Nisa, lib/wheelFind). The option in the middle band is the one Enter picks.
 *
 * Same words as ui/Segmented: options [{ id, label, hint?, keys?, disabled? }],
 * value is the chosen id, onChange gets the new one. hint prints faint at the
 * right (an Arabic name, say), keys are extra words typing may match, and a
 * disabled option shows but cannot be picked.
 * narrow: a numbers-only wheel (ayah, juz) gets a slim card and a "No." hint.
 * accent: the tab's colour, for the middle band and the focused type box.
 * arabic: the labels are Arabic words. readOnly: shows the choice, stays in the
 * tab order, does not open (a marked answer).
 */
import { useEffect, useId, useRef, useState } from 'react'

import { wheelFind } from '../../lib/wheelFind'
import theme from '../../theme.json'
import ArabicText from './ArabicText'

// Card height in px (input, five wheel rows, padding) with a little air.
const CARD_HEIGHT = 280

export default function WheelPicker({ label, placeholder, options, value, onChange, disabled = false, readOnly = false, narrow = false, arabic = false, accent, className = '' }) {
  const [open, setOpen] = useState(false)
  const [typed, setTyped] = useState('')
  const [at, setAt] = useState(0)
  const [up, setUp] = useState(false)
  const box = useRef(null)
  const pill = useRef(null)
  const wheel = useRef(null)
  const typeBox = useRef(null)
  // While the wheel spins itself to a typed match, scroll events are its own, not a hand.
  const steering = useRef(false)
  const id = useId()
  const n = options.length
  const typeable = n >= theme.wheel['type-from']
  // A long enough list loops: drawn three times, kept to the middle copy, so its last choices sit above its first.
  const loop = n >= theme.wheel['loop-from']
  const rows = loop ? [...options, ...options, ...options] : options
  const home = loop ? n : 0

  const chosen = options.find((o) => o.id === value)
  const text = (words) => (arabic ? <ArabicText size="base">{words}</ArabicText> : words)

  const spin = (index, smooth = true) => {
    const list = wheel.current
    const item = list?.children[index]
    if (!item) return
    setAt(index)
    steering.current = smooth
    list.scrollTo({ top: item.offsetTop - list.clientHeight / 2 + item.offsetHeight / 2, behavior: smooth ? 'smooth' : 'instant' })
  }

  const close = (refocus) => { setOpen(false); setTyped(''); if (refocus) pill.current?.focus() }
  const pick = (row) => { const o = options[row % n]; if (o && !o.disabled) { onChange(o.id); close(true) } }

  // On opening, the wheel starts at the chosen option, keys going to the type box or the wheel.
  useEffect(() => {
    if (!open) return
    spin(home + Math.max(0, options.findIndex((o) => o.id === value)), false)
    ;(typeBox.current ?? wheel.current)?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  useEffect(() => {
    if (!open) return undefined
    const outside = (event) => { if (!box.current?.contains(event.target)) close(false) }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])

  // A row outside the middle copy jumps, unseen, to the same choice inside it.
  const recentre = (row) => {
    const shift = row < home ? n : row >= home + n ? -n : 0
    if (shift) wheel.current.scrollTop += shift * wheel.current.children[0].offsetHeight
    return row + shift
  }

  // Spinning by hand moves the middle band too.
  const onScroll = () => {
    if (steering.current) return
    const list = wheel.current
    const first = list?.children[0]
    if (!first) return
    const middle = list.scrollTop + list.clientHeight / 2 - first.offsetTop
    setAt(recentre(Math.min(rows.length - 1, Math.max(0, Math.floor(middle / first.offsetHeight)))))
  }

  const onKeyDown = (event) => {
    const step = { ArrowDown: 1, ArrowUp: -1 }[event.key]
    if (step) { event.preventDefault(); spin(Math.min(rows.length - 1, Math.max(0, recentre(at) + step))) }
    else if (event.key === 'Enter') { event.preventDefault(); pick(at) }
    else if (event.key === 'Escape') { event.preventDefault(); close(true) }
  }

  const onType = (text) => {
    setTyped(text)
    const found = wheelFind(options, text)
    if (found >= 0) spin(home + found)
  }

  // Hangs from the pill's left edge, or from its right edge when it would cross
  // the screen's, kept as far in as the pill is. Layout width, not the animated
  // box, which starts the rise scaled down.
  const fit = (card) => {
    if (!card) return
    const { left, right } = box.current.getBoundingClientRect()
    const room = document.documentElement.clientWidth
    const gap = Math.min(left, room - right)
    const x = left + card.offsetWidth > room - gap ? right - card.offsetWidth : left
    card.style.translate = `${Math.max(gap, x) - left}px 0`
  }

  return (
    <div ref={box} className={`relative ${className}`.trim()} style={accent ? { '--c': accent } : undefined}>
      <button
        ref={pill}
        type="button"
        aria-label={label}
        aria-haspopup={readOnly ? undefined : 'listbox'}
        aria-expanded={readOnly ? undefined : open}
        aria-disabled={readOnly || undefined}
        disabled={disabled}
        onClick={() => {
          if (readOnly) return
          const at = pill.current.getBoundingClientRect()
          // Opens upwards when the card would run off the bottom and there is more room above.
          const below = window.innerHeight - at.bottom
          setUp(below < CARD_HEIGHT && at.top > below)
          setOpen((o) => !o)
        }}
        className="wheel-pill press"
      >
        <span className={chosen ? '' : 'text-[var(--text-dim)]'}>{chosen ? text(chosen.label) : placeholder}</span>
        <svg aria-hidden="true" viewBox="0 0 24 24" className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M8 9l4-4 4 4M8 15l4 4 4-4" />
        </svg>
      </button>

      {open && (
        <div ref={fit} onKeyDown={onKeyDown} className={`wheel-card rise-in ${narrow ? 'wheel-card-narrow' : ''} ${up ? 'wheel-card-up' : ''}`}>
          {typeable && (
            <input
              ref={typeBox}
              role="combobox"
              aria-label={`Find a ${label.toLowerCase()}`}
              aria-controls={id}
              aria-expanded="true"
              aria-activedescendant={`${id}-${at}`}
              value={typed}
              onChange={(e) => onType(e.target.value)}
              placeholder={narrow ? 'No.' : 'Type to find'}
              className="wheel-type"
            />
          )}
          <div className="wheel-window">
            <ul ref={wheel} id={id} role="listbox" aria-label={label} tabIndex={-1} aria-activedescendant={typeable ? undefined : `${id}-${at}`} onScroll={onScroll} onScrollEnd={() => { steering.current = false; setAt(recentre(at)) }} onWheel={() => { steering.current = false }} onTouchStart={() => { steering.current = false }} className="wheel-list">
              {rows.map((o, i) => (
                <li
                  key={`${i}`}
                  aria-hidden={(loop && (i < home || i >= home + n)) || undefined}
                  id={`${id}-${i}`}
                  role="option"
                  aria-selected={i === at}
                  aria-disabled={o.disabled || undefined}
                  onClick={() => pick(i)}
                  className="wheel-item"
                >
                  <span className="truncate">{text(o.label)}</span>
                  {o.hint && <ArabicText size="tiny" className="wheel-hint">{o.hint}</ArabicText>}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
