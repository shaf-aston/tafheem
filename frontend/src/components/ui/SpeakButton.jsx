/**
 * Hear this word. A small speaker icon; lib/speak.js picks the voice.
 */
import { useEffect, useRef, useState } from 'react'

import { prepare, speak, stop } from '../../lib/speak'

// `ref` reaches the button itself, so a keyboard shortcut can press it; `shortcut`
// names that key in the tooltip. `early` readies the voice on arrival, for a
// button that is the point of its view; others ready it on hover or focus.
export default function SpeakButton({ text, ref, shortcut, early, className = '' }) {
  // idle | busy (finding a voice) | speaking | failed
  const [state, setState] = useState('idle')

  // Whether the sound playing is this button's, and whether it is still on screen.
  const mine = useRef(false)
  const alive = useRef(true)

  useEffect(() => { if (early) prepare(text) }, [early, text])

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
  return (
    <button
      ref={ref}
      type="button"
      onClick={press}
      onPointerEnter={() => prepare(text)}
      onFocus={() => prepare(text)}
      aria-label={state === 'speaking' ? 'Stop' : state === 'failed' ? FAILED : 'Say it aloud'}
      title={state === 'failed' ? FAILED : shortcut ? `Say it aloud (${shortcut})` : 'Say it aloud'}
      aria-busy={state === 'busy'}
      className={`shrink-0 w-7 h-7 grid place-items-center rounded-full border transition-colors ${look}
        ${state === 'busy' ? 'animate-pulse' : ''} ${className}`}
    >
      <SpeakerGlyph />
    </button>
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
