/**
 * The answer to an English search: the Arabic words that carry that meaning.
 *
 * A different question from the other direction, and so a different shape. Under
 * Arabic the reader has one word and wants everything it means; under English
 * they have a meaning and want to see which words carry it, which means seeing
 * the candidates side by side rather than scrolling one full entry at a time.
 * "spirit" returns ten words holding thirty-one senses between them, and as full
 * entries that was a page and a half of scrolling to compare two words.
 *
 * So each word is one small card showing only the sense that answered the search
 * (the sense carrying the word typed; the API does not say which one matched, so
 * it is found in the text), with the word's other senses folded.
 *
 * Two ways to open, because they answer two wants. Pressing a card opens that
 * word, for a reader following one word. Pressing its "+n senses" opens every
 * card on the same line, because one card grown to seven senses beside two that
 * stayed at one is what made the short ones look empty.
 *
 * Which cards share a line is measured, never assumed: the grid decides how many
 * fit from the width of the window, so the cards that came out at the same top
 * are the line.
 */
import { useRef, useState } from 'react'

import { plainPronunciation } from '../../lib/pronounce'

import ArabicText from './ArabicText'
import Pronunciation from './Pronunciation'
import RootActions from './RootActions'

/** The sense that answered the search, and the rest of them. */
function splitSenses(definitions, query) {
  const needle = query.trim().toLowerCase()
  // Read into English letters first, so a sense saying (kātaba) never sits under
  // a card whose pronunciation line says kaataba.
  const senses = definitions.map((d) => plainPronunciation(d))
  const lead = senses.find((d) => d.toLowerCase().includes(needle)) ?? senses[0] ?? ''
  return { lead, rest: senses.filter((d) => d !== lead) }
}

export default function WordGrid({ results, query, accent, onGo }) {
  const grid = useRef(null)
  const [open, setOpen] = useState(() => new Set())

  const toggle = (i) =>
    setOpen((was) => {
      const next = new Set(was)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })

  // Every card that came out at the same top as this one, opened or closed
  // together so a line never ends in a card of empty space.
  const toggleLine = (i) => {
    const cards = [...(grid.current?.children ?? [])]
    const mine = cards[i]
    if (!mine) return toggle(i)
    const line = cards
      .map((card, n) => [card, n])
      .filter(([card]) => Math.abs(card.offsetTop - mine.offsetTop) < 2)
      .map(([, n]) => n)

    setOpen((was) => {
      const next = new Set(was)
      const opening = !was.has(i)
      line.forEach((n) => (opening ? next.add(n) : next.delete(n)))
      return next
    })
  }

  return (
    <div ref={grid} className="grid gap-3 sm:grid-cols-[repeat(auto-fill,minmax(17rem,1fr))]">
      {results.map((entry, i) => (
        <Word
          key={`${entry.arabic}-${entry.root || i}`}
          entry={entry}
          query={query}
          accent={accent}
          i={i}
          open={open.has(i)}
          onGo={onGo}
          onToggle={() => toggle(i)}
          onToggleLine={() => toggleLine(i)}
        />
      ))}
    </div>
  )
}

function Word({ entry, query, accent, i, open, onGo, onToggle, onToggleLine }) {
  const { lead, rest } = splitSenses(entry.definitions ?? [], query)
  const foldable = rest.length > 0

  // Pressing anywhere on the card opens that one word, so a reader following a
  // single word does not have to find a particular thing to press. The card is
  // not itself a button: it carries the buttons that send the root to another
  // tab, and a button inside a button is not valid markup. The sense below is
  // the real control, which is what the keyboard reaches and what a screen
  // reader announces; the rest of the card is a wider target for a mouse.
  const press = (event) => {
    if (!foldable || event.target.closest('[data-inner]')) return
    onToggle()
  }

  return (
    <div
      onClick={press}
      style={{ '--i': i, '--c': accent }}
      className={`rise-in lift p-4 rounded-[var(--radius-md)] bg-[var(--surface)]
        border border-[var(--border)] transition-colors flex flex-col gap-2
        focus-visible:border-[var(--c)] focus-visible:outline-none
        ${foldable ? 'cursor-pointer hover:border-[var(--border-hi)]' : ''}`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <ArabicText style={{ color: accent }}>{entry.arabic}</ArabicText>
        <Pronunciation>{entry.transliteration}</Pronunciation>
      </div>

      {foldable ? (
        <button
          data-inner
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          title="Open this word's other senses"
          className="text-start text-sm text-[var(--text)]
            focus-visible:outline-none focus-visible:underline
            decoration-[var(--c)] underline-offset-4"
        >
          {lead}
        </button>
      ) : (
        <div className="text-sm text-[var(--text)]">{lead}</div>
      )}

      {open && (
        <ul className="text-sm text-[var(--text-dim)] space-y-1">
          {rest.map((d) => <li key={d}>{d}</li>)}
        </ul>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2 mt-auto pt-1">
        <span data-inner>
          <RootActions root={entry.root} onGo={onGo} exclude="dict" />
        </span>

        {foldable && (
          <button
            data-inner
            type="button"
            onClick={onToggleLine}
            aria-expanded={open}
            title="Open this one and the others on its line together"
            className="type-small leading-none px-2 py-1 rounded-full shrink-0 ms-auto
              border border-[var(--border)] text-[var(--text-faint)]
              hover:border-[var(--c)] hover:text-[var(--text)] transition-colors"
          >
            {open ? 'Fewer' : `+${rest.length} ${rest.length === 1 ? 'sense' : 'senses'}`}
          </button>
        )}
      </div>
    </div>
  )
}
