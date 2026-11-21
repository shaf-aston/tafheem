/**
 * One word of a page's line: its English on hover, the dictionary on a click.
 *
 * Hover or focus shows what the grammar read in the word, above it: its English,
 * the word it comes from, and its role. A click (Enter from the keyboard) looks
 * it up in the dictionary. A finger has no hover, so the first tap shows the
 * same and its Look up button is the click. The text stays plain text, a span
 * among spaces, so a reader can select a run of words and copy it whole.
 *
 * The note is kept on screen: near either edge it is slid back in rather than
 * cut off or pushing the page wider.
 */
import { useLayoutEffect, useRef, useState } from 'react'

import ArabicText from '../ui/text/ArabicText'

const EDGE = 12

export default function PageWord({ word, onLookup }) {
  const [open, setOpen] = useState(false)
  const touch = useRef(false)
  // Whether the note was open when the finger came down: a tap's focus opens it before its click lands.
  const wasOpen = useRef(false)
  const note = useRef(null)
  const [shift, setShift] = useState(0)

  useLayoutEffect(() => {
    if (!open || !note.current) return setShift(0)
    const { left, right } = note.current.getBoundingClientRect()
    const width = document.documentElement.clientWidth
    setShift(left < EDGE ? EDGE - left : right > width - EDGE ? width - EDGE - right : 0)
  }, [open])

  const lookUp = () => { setOpen(false); onLookup(word.base || word.arabic) }
  const about = [word.lemma && word.lemma !== word.arabic ? word.lemma : '', word.role || word.pos].filter(Boolean)

  return (
    <span
      className="page-word relative inline-block"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <span
        role="button"
        tabIndex={0}
        aria-expanded={open}
        aria-label={`${word.arabic}: ${word.english || 'look it up'}`}
        onPointerDown={(event) => { touch.current = event.pointerType === 'touch'; wasOpen.current = open }}
        onClick={() => (touch.current && !wasOpen.current ? setOpen(true) : lookUp())}
        onKeyDown={(event) => { if (event.key === 'Enter') lookUp(); if (event.key === 'Escape') setOpen(false) }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className={`rounded-[var(--radius-sm)] px-0.5 cursor-pointer transition-colors outline-none
          focus-visible:ring-2 focus-visible:ring-[var(--c)] ${open ? 'bg-[var(--surface-hi)] text-[var(--c)]' : 'hover:text-[var(--c)]'}`}
      >
        {word.arabic}
      </span>
      {open && (
        <span
          ref={note}
          role="tooltip"
          dir="ltr"
          style={{ transform: `translateX(calc(-50% + ${shift}px))` }}
          className="rise-in absolute bottom-full left-1/2 mb-1.5 z-[var(--layer-tip)] w-max max-w-[min(16rem,calc(100vw-2rem))]
            flex flex-col items-center gap-0.5 px-3 py-2 rounded-[var(--radius-md)] text-center
            bg-[var(--surface-hi)] border border-[var(--border-hi)] shadow-[var(--shadow-pop)]"
        >
          <span className="type-body text-[var(--text)] leading-snug" lang="en">{word.english || 'No English for this word'}</span>
          {about.length > 0 && (
            <ArabicText size="sm" className="text-[var(--text-dim)]">{about.join(' · ')}</ArabicText>
          )}
          {/* The finger's way to the dictionary, the mouse's being the click itself. */}
          <button
            type="button"
            onMouseDown={(event) => event.preventDefault()}
            onClick={lookUp}
            className="type-label underline text-[var(--text-dim)] hover:text-[var(--text)]"
          >
            Look up
          </button>
        </span>
      )}
    </span>
  )
}
