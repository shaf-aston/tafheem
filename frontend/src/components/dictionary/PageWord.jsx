/**
 * One word of a page's line: pointed at, it shows in the reader's word bar; clicked, it is looked up.
 *
 * Hover or keyboard focus chooses the word, and the bar at the foot of the
 * reader (PageWordBar) shows what the grammar read in it. A click, or Enter,
 * looks it up in the dictionary. A finger has no hover, so its first tap only
 * chooses the word and the bar's own Look up button is the way on. The word
 * stays plain text, a span among spaces, so a reader can select a run of words
 * and copy it whole.
 *
 * One bar for the whole page rather than a note floating over each word: a note
 * covered the line above, ran off the side of a phone, vanished when the mouse
 * crossed the gap to its button, and took the focus with it.
 */
import { useRef } from 'react'

export default function PageWord({ word, chosen, onChoose, onLookup }) {
  // Whether the word was already chosen when the finger came down: a tap's focus chooses it before its click lands.
  const wasChosen = useRef(false)
  const touch = useRef(false)
  const lookUp = () => (onLookup ? onLookup(word.base || word.arabic) : onChoose())

  return (
    <span
      role="button"
      tabIndex={0}
      aria-label={`${word.arabic}: ${word.english || 'look it up'}`}
      aria-pressed={chosen}
      onMouseEnter={() => onChoose()}
      onFocus={() => onChoose()}
      onPointerDown={(event) => { touch.current = event.pointerType === 'touch'; wasChosen.current = chosen }}
      onClick={() => (touch.current && !wasChosen.current ? onChoose() : lookUp())}
      onKeyDown={(event) => { if (event.key === 'Enter') lookUp() }}
      className={`page-word rounded-[var(--radius-sm)] px-0.5 cursor-pointer transition-colors outline-none
        focus-visible:ring-2 focus-visible:ring-[var(--c)] ${chosen ? 'bg-[var(--surface-hi)] text-[var(--c)]' : 'hover:text-[var(--c)]'}`}
    >
      {word.arabic}
    </span>
  )
}
