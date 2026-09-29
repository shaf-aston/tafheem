/**
 * Hear this word. A small speaker icon; lib/speak.js picks the voice.
 *
 * Styled like PlayAyah, its sibling, so the two sound buttons read as one
 * family. The voice that spoke is named beside it while it talks, so a
 * computer voice is never mistaken for a reciter.
 */
import { useEffect, useRef, useState } from 'react'

import { speak, stop } from '../../lib/speak'

export default function SpeakButton({ text, className = '' }) {
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
  const label = state === 'speaking' ? credit : state === 'failed' ? 'No voice could say this word' : ''
  return (
    // The label hangs beside the icon rather than inside the row, so a centred
    // icon stays put when the label comes and goes.
    <span className={`relative inline-flex ${className}`}>
      <button
        type="button"
        onClick={press}
        aria-label={state === 'speaking' ? 'Stop' : 'Say it aloud'}
        title={state === 'failed' ? 'No voice could say this word' : 'Say it aloud'}
        aria-busy={state === 'busy'}
        className={`shrink-0 w-7 h-7 grid place-items-center rounded-full border transition-colors ${look}
          ${state === 'busy' ? 'animate-pulse' : ''}`}
      >
        <SpeakerGlyph />
      </button>
      {/* Always mounted, so a screen reader announces the text when it changes. */}
      <span aria-live="polite" className={`absolute start-full ms-2 top-1/2 -translate-y-1/2 whitespace-nowrap type-tiny
        ${state === 'failed' ? 'text-[var(--warn)]' : 'text-[var(--text-faint)]'}`}>{label}</span>
    </span>
  )
}

function SpeakerGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor" />
      <path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11" />
    </svg>
  )
}
