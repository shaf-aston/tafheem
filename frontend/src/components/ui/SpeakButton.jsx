/**
 * Hear this word. A small speaker icon; lib/speak.js picks the voice.
 *
 * Styled like PlayAyah, its sibling, so the two sound buttons read as one
 * family. The voice that spoke is named beside it while it talks, so a
 * computer voice is never mistaken for a reciter.
 */
import { useEffect, useRef, useState } from 'react'

import { speak, stop } from '../../lib/speak'

// `ref` reaches the button itself, so a keyboard shortcut can press it; `shortcut`
// names that key in the tooltip. `inline` puts the voice's name in the row, for a
// tight spot (a chat bubble) where a name hanging beside would be cut off: 'end'
// after the icon, 'start' before it, whichever side the row is not anchored to,
// so the icon stays under the finger when the name appears.
export default function SpeakButton({ text, ref, shortcut, inline, className = '' }) {
  // idle | busy (finding a voice) | speaking | failed
  const [state, setState] = useState('idle')
  const [credit, setCredit] = useState('')

  // Whether the sound playing is this button's, and whether it is still on screen.
  const mine = useRef(false)
  const alive = useRef(true)

  // Leaving (a new word) silences this button's word, never another's or an ayah.
  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
      if (mine.current) stop()
    }
  }, [text])

  const press = async () => {
    if (state === 'busy') return
    if (state === 'speaking') return stop()
    setState('busy')
    mine.current = true
    try {
      const voice = await speak(text)
      if (!alive.current) return stop()
      setCredit(voice.credit)
      setState('speaking')
      await voice.done
      if (alive.current) setState('idle')
    } catch (err) {
      if (alive.current) setState(err.interrupted ? 'idle' : 'failed')
    } finally {
      mine.current = false
    }
  }

  const look = state === 'failed'
    ? 'text-[var(--warn)] border-[var(--warn)]'
    : state === 'idle'
      ? 'text-[var(--text-faint)] border-[var(--border)] hover:text-[var(--text)] hover:border-[var(--border-hi)]'
      : 'text-[var(--primary)] border-[var(--primary)]'
  const label = state === 'speaking' ? credit : state === 'failed' ? FAILED : ''
  return (
    // By default the label hangs beside the icon rather than inside the row, so
    // a centred icon stays put when the label comes and goes.
    <span className={`relative inline-flex items-center ${inline === 'start' ? 'flex-row-reverse' : ''} ${className}`}>
      <button
        ref={ref}
        type="button"
        onClick={press}
        aria-label={state === 'speaking' ? 'Stop' : 'Say it aloud'}
        title={state === 'failed' ? FAILED : shortcut ? `Say it aloud (${shortcut})` : 'Say it aloud'}
        aria-busy={state === 'busy'}
        className={`shrink-0 w-7 h-7 grid place-items-center rounded-full border transition-colors ${look}
          ${state === 'busy' ? 'animate-pulse' : ''}`}
      >
        <SpeakerGlyph />
      </button>
      {/* Always mounted, so a screen reader announces the text when it changes. */}
      <span aria-live="polite" className={`${inline ? (label ? (inline === 'start' ? 'me-2' : 'ms-2') : '') : 'absolute start-full ms-2 top-1/2 -translate-y-1/2'} whitespace-nowrap type-tiny
        ${state === 'failed' ? 'text-[var(--warn)]' : 'text-[var(--text-faint)]'}`}>{label}</span>
    </span>
  )
}

const FAILED = 'No voice could say this'

function SpeakerGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor" />
      <path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11" />
    </svg>
  )
}
