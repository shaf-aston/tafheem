/**
 * A run of hadiths, each with its grading, a copy button and a star. One list
 * for a book, for search hits and for the Starred view, so all three behave
 * the same.
 *
 * Collection names and which are Sahih come from useHadithCollections. A book's
 * own list passes `collection`, since its rows do not say which; there
 * the label is the number alone, and a Sahih book's cards carry no grading
 * because the green dot by the collection's name says it once for all of them.
 * Without it (search, Starred) hadiths from several collections meet, so the
 * label names the collection and every card carries its grading.
 * Narrators come from each card's own book (lib/useNarrators), so names are tappable and the
 * family fold shows in a book, in search and in Starred alike. So do the weak points: a hadith
 * whose chain has any carries one quiet "2 weak points" chip that opens the drawing, where each
 * weak narrator is marked and ranked and each doubtful link lettered (lib/weak); a hadith that classical
 * books speak of carries a "Scholars" chip to the same drawing, where their words are quoted.
 * `onNarrator` opens one narrator's full page; `onHadith` opens a sibling narration of the same number.
 */
import { useState } from 'react'

import { useHadithCollections } from '../lib/useHadithCollections'
import { useHadithFavorites } from '../lib/useHadithFavorites'
import { useKin, useNarrators, useWeakNotes } from '../lib/useNarrators'
import { drawnChain } from '../lib/rijal'
import { weakLinks, weakPoints } from '../lib/weak'

import ChainSheet from './ui/ChainSheet'
import Chip from './ui/Chip'
import CopyButton from './ui/CopyButton'
import FavoriteStar from './ui/FavoriteStar'
import GradeMark from './ui/GradeMark'
import HadithText from './ui/HadithText'
import NarrationFamily from './ui/NarrationFamily'
import NarratorSheet from './ui/NarratorSheet'

export default function HadithCards({ items, accent, collection, columns = false, hideChain = false, onNarrator, onHadith }) {
  const { isFavorite, toggle } = useHadithFavorites()
  const { of } = useHadithCollections()
  const books = items.map((h) => ({ collection: h.collection ?? collection, book: h.book }))
  const namesOf = useNarrators(books)
  const weakOf = useWeakNotes(books)
  const kinOf = useKin(books)
  // The hadith whose chain is drawn in the pop-up, if any.
  const [drawn, setDrawn] = useState(null)
  // The narrator whose sheet is open, if any.
  const [who, setWho] = useState(null)

  /** One hadith's drawn chain with its weak narrators ranked, its doubtful links lettered, and the scale they sit on. */
  const drawing = (h) => {
    const ref = `${h.number}${h.part ?? ''}`
    const { notes, links: ties, rulings, rules, scale } = weakOf(h, ref)
    // A hadith with no chain to draw still has what scholars said of it.
    if (!h.cut) return { links: [], scale, rulings, weak: [], linkPoints: [], chainless: true }
    const links = drawnChain(h.arabic, h.cut, namesOf(h)[ref] ?? [], notes, ties)
    return { links, scale, rulings, weak: weakPoints(links, scale), linkPoints: weakLinks(links, rules) }
  }

  return (
    <>
      <ul className={`list-none m-0 p-0 ${columns ? 'grid gap-2 items-start md:grid-cols-2' : 'space-y-2'}`}>
        {items.map((item, i) => {
          const h = { ...item, collection: item.collection ?? collection }
          const ref = `${h.number}${h.part ?? ''}`
          const names = namesOf(h)
          const found = weakOf(h, ref)
          const { weak, linkPoints, rulings } = found.notes.length + found.links.length + found.rulings.length ? drawing(h) : { weak: [], linkPoints: [], rulings: [] }
          const points = weak.length + linkPoints.length
          const kin = kinOf(h)
          return (
            <HadithText
              key={`${h.collection}:${ref}`}
              id={`hadith-${ref}`}
              index={i}
              label={collection ? ref : `${of(h.collection).short} ${ref}`}
              arabic={h.arabic}
              cut={h.cut}
              english={h.english}
              accent={accent}
              hideChain={hideChain}
              names={names[ref]}
              onNarrator={setWho}
              footer={kin > 1 && !hideChain && (
                <NarrationFamily
                  collection={h.collection} number={h.number} part={h.part} count={kin} accent={accent}
                  onOpen={(p) => onHadith?.({ collection: h.collection, book: p.book, number: h.number, part: p.part })}
                  onNarrator={setWho}
                />
              )}
              action={(
                <span className="flex flex-wrap items-center justify-end gap-2">
                  {!(collection && of(collection).sahih) && (
                    <GradeMark grades={h.grades} sahihBy={of(h.collection).sahih ? of(h.collection).name : null} cite={h.cite} />
                  )}
                  {points > 0 && (
                    <Chip quiet tinted accent={accent} onClick={() => setDrawn(h)}>
                      {points} weak point{points > 1 && 's'}
                    </Chip>
                  )}
                  {rulings.length > 0 && (
                    <Chip quiet tinted accent={accent} onClick={() => setDrawn(h)}>
                      Scholars
                    </Chip>
                  )}
                  {h.cut && (
                    <button
                      type="button"
                      onClick={() => setDrawn(h)}
                      title="Draw the chain"
                      aria-label="Draw the chain"
                      className="press tap shrink-0 grid place-items-center text-[var(--text-faint)] hover:text-[var(--text-dim)] transition-colors"
                    >
                      <svg aria-hidden="true" viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <circle cx="12" cy="4" r="2" />
                        <circle cx="6" cy="20" r="2" />
                        <circle cx="18" cy="20" r="2" />
                        <path d="M12 6v5M12 11l-6 7M12 11l6 7" />
                      </svg>
                    </button>
                  )}
                  <CopyButton small label="Copy" text={[h.arabic, h.english].filter(Boolean).join('\n\n')} />
                  <FavoriteStar on={isFavorite(h)} onClick={() => toggle(h)} />
                </span>
              )}
            />
          )
        })}
      </ul>
      {who != null && <NarratorSheet id={who} onClose={() => setWho(null)} onOpenPage={onNarrator} />}
      {drawn && (
        <ChainSheet
          {...drawing(drawn)}
          onNarrator={(id) => { setDrawn(null); setWho(id) }}
          author={of(drawn.collection).short}
          accent={accent}
          onClose={() => setDrawn(null)}
        />
      )}
    </>
  )
}
