/**
 * A topic's notes as flashcards, one at a time.
 *
 * The cards are the note's own marks (lib/notes.js cardsOf), so there is no
 * deck to keep in step with the notes. The reader turns a card, then says
 * whether they knew it; the ones they did not come round again at the end.
 * Self-marked on purpose: typing Arabic with its harakat to be graded by a
 * string match would fail readers who know the answer.
 */
import { useEffect, useRef, useState } from 'react'

import { NOTES, runOf } from '../lib/notes'

import ArabicText from './ui/ArabicText'
import EmptyState from './ui/EmptyState'
import PrimaryButton from './ui/PrimaryButton'
import SmallButton from './ui/SmallButton'

// Arabic cards are right to left, English ones are not; a card says which by its letters.
const isArabic = (text) => /[؀-ۿ]/.test(text)

// A whole paragraph at the large size fills the screen; only a short card gets it.
const LONG_CARD = 80

function Face({ text }) {
  const size = text.length > LONG_CARD ? 'base' : 'lg'
  return isArabic(text)
    ? <ArabicText as="p" size={size} className="leading-loose">{text}</ArabicText>
    : <p className="type-body">{text}</p>
}

export default function NoteCards({ cards, accent, onPage }) {
  // Where the current run starts in the whole topic, so "next" carries on from it
  // even after a round of only the missed ones.
  const [from, setFrom] = useState(0)
  const [deck, setDeck] = useState(() => runOf(cards))
  const [at, setAt] = useState(0)
  const [turned, setTurned] = useState(false)
  const [missed, setMissed] = useState([])
  // The main button moves (Show, then Knew it, then the next Show); focus goes
  // with it so a keyboard reader can drill with Enter alone.
  const main = useRef(null)
  useEffect(() => { main.current?.querySelector('button')?.focus() }, [at, turned])

  if (!cards.length) {
    return <EmptyState>Nothing on this topic is marked for the switches that are on. Turn another one on above.</EmptyState>
  }

  const card = deck[at]
  const answer = (knew) => {
    if (!knew) setMissed((list) => [...list, card])
    setTurned(false)
    setAt((n) => n + 1)
  }

  if (!card) {
    const again = () => { setDeck(missed); setMissed([]); setAt(0) }
    const after = from + NOTES.cardsPerRun
    const coming = runOf(cards, after)
    const next = () => { setFrom(after); setDeck(coming); setMissed([]); setAt(0) }
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-5 space-y-3 text-center">
        <p className="font-medium">
          {missed.length ? `${deck.length - missed.length} of ${deck.length} known` : `All ${deck.length} known`}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {missed.length > 0 && <SmallButton onClick={again}>Again with the {missed.length} I missed</SmallButton>}
          {coming.length > 0 && <SmallButton onClick={next}>Next {coming.length} cards</SmallButton>}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3" style={{ '--c': accent }}>
      <div aria-live="polite" className="space-y-3">
      <p className="type-small text-[var(--text-faint)]">Card {at + 1} of {deck.length}</p>
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-5 space-y-4 min-h-40">
        <Face text={card.front} />
        {turned && (
          <div className="border-t border-[var(--border)] pt-4 fade-in">
            <Face text={card.back} />
          </div>
        )}
      </div>
      </div>
      <div className="flex items-center justify-between gap-3">
        <SmallButton onClick={() => onPage(card.page)}>See it in the notes</SmallButton>
        <div className="flex items-center gap-2">
          {turned ? (
            <>
              <SmallButton onClick={() => answer(false)}>Didn&apos;t know</SmallButton>
              <div ref={main} className="w-32"><PrimaryButton accent={accent} onClick={() => answer(true)}>Knew it</PrimaryButton></div>
            </>
          ) : (
            <div ref={main} className="w-32"><PrimaryButton accent={accent} onClick={() => setTurned(true)}>Show</PrimaryButton></div>
          )}
        </div>
      </div>
    </div>
  )
}
