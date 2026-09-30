/**
 * A pill that opens a small floating wheel of choices: spin it, or type and it
 * spins there ("nis" or "4" lands on An-Nisa, lib/wheelFind). The option in the
 * middle band is the one Enter picks. Meant to replace any long <select>.
 *
 * options: [{ value, label, hint?, keys? }]; hint prints faint at the right
 * (an Arabic name, say) and keys are extra words typing may match.
 * narrow: a numbers-only wheel (ayah, juz) gets a slim card and a "No." hint.
 */
import { useEffect, useId, useRef, useState } from 'react'

import { wheelFind } from '../../lib/wheelFind'
import ArabicText from './ArabicText'

// Card height in px (input, five wheel rows, padding) with a little air.
const CARD_HEIGHT = 280

export default function WheelPicker({ label, placeholder, options, value, onPick, disabled = false, narrow = false, className = '' }) {
  const [open, setOpen] = useState(false)
  const [typed, setTyped] = useState('')
  const [at, setAt] = useState(0)
  const [flip, setFlip] = useState(false)
  const [up, setUp] = useState(false)
  const box = useRef(null)
  const pill = useRef(null)
  const wheel = useRef(null)
  // While the wheel spins itself to a typed match, scroll events are its own, not a hand.
  const steering = useRef(false)
  const id = useId()

  const chosen = options.find((o) => o.value === value)

  const spin = (index, smooth = true) => {
    const list = wheel.current
    const item = list?.children[index]
    if (!item) return
    setAt(index)
    steering.current = smooth
    list.scrollTo({ top: item.offsetTop - list.clientHeight / 2 + item.offsetHeight / 2, behavior: smooth ? 'smooth' : 'instant' })
  }

  const close = (refocus) => { setOpen(false); setTyped(''); if (refocus) pill.current?.focus() }
  const pick = (index) => { const o = options[index]; if (o) { onPick(o.value); close(true) } }

  // On opening, the wheel starts at the chosen option.
  useEffect(() => {
    if (open) spin(Math.max(0, options.findIndex((o) => o.value === value)), false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  useEffect(() => {
    if (!open) return undefined
    const outside = (event) => { if (!box.current?.contains(event.target)) close(false) }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])

  // Spinning by hand moves the middle band too.
  const onScroll = () => {
    if (steering.current) return
    const list = wheel.current
    const first = list?.children[0]
    if (!first) return
    const middle = list.scrollTop + list.clientHeight / 2 - first.offsetTop
    setAt(Math.min(options.length - 1, Math.max(0, Math.floor(middle / first.offsetHeight))))
  }

  const onKeyDown = (event) => {
    const step = { ArrowDown: 1, ArrowUp: -1 }[event.key]
    if (step) { event.preventDefault(); spin(Math.min(options.length - 1, Math.max(0, at + step))) }
    else if (event.key === 'Enter') { event.preventDefault(); pick(at) }
    else if (event.key === 'Escape') { event.preventDefault(); close(true) }
  }

  const onType = (text) => {
    setTyped(text)
    const found = wheelFind(options, text)
    if (found >= 0) spin(found)
  }

  return (
    <div ref={box} className={`relative ${className}`.trim()}>
      <button
        ref={pill}
        type="button"
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => {
          // Opens leftwards when a pill sits too near the right edge for the card.
          const at = pill.current.getBoundingClientRect()
          setFlip(at.left + (narrow ? 144 : 256) > window.innerWidth)
          // Opens upwards when the card would run off the bottom and there is more room above.
          const below = window.innerHeight - at.bottom
          setUp(below < CARD_HEIGHT && at.top > below)
          setOpen((o) => !o)
        }}
        className="wheel-pill press"
      >
        <span className={chosen ? '' : 'text-[var(--text-dim)]'}>{chosen?.label ?? placeholder}</span>
        <svg aria-hidden="true" viewBox="0 0 24 24" className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M8 9l4-4 4 4M8 15l4 4 4-4" />
        </svg>
      </button>

      {open && (
        <div className={`wheel-card rise-in ${narrow ? 'wheel-card-narrow' : ''} ${flip ? 'wheel-card-flip' : ''} ${up ? 'wheel-card-up' : ''}`}>
          <input
            autoFocus
            role="combobox"
            aria-label={`Type a ${label.toLowerCase()} ${narrow ? 'number' : 'name or number'}`}
            aria-controls={id}
            aria-expanded="true"
            aria-activedescendant={`${id}-${at}`}
            value={typed}
            onChange={(e) => onType(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={narrow ? 'No.' : 'No. or name'}
            className="wheel-type"
          />
          <div className="wheel-window">
            <ul ref={wheel} id={id} role="listbox" aria-label={label} onScroll={onScroll} onScrollEnd={() => { steering.current = false }} onWheel={() => { steering.current = false }} onTouchStart={() => { steering.current = false }} className="wheel-list">
              {options.map((o, i) => (
                <li
                  key={o.value}
                  id={`${id}-${i}`}
                  role="option"
                  aria-selected={i === at}
                  onClick={() => pick(i)}
                  className="wheel-item"
                >
                  <span className="truncate">{o.label}</span>
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
