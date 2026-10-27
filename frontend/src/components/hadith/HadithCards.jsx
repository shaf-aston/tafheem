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
 * family fold shows in a book, in search and in Starred alike. Each hadith with a chain carries one quiet
 * "Chain" chip ("Chain · 2 weak" where it has weak points) that opens the sheet (hadith/ChainSheet): the chain drawn,
 * its weak points ranked and doubtful links lettered (lib/weak), what classical books say of it and the words, one
 * tab each; a hadith with no chain that those books speak of carries "Verdicts" to the same sheet.
 * Under each one's words, its reference as sunnah.com prints it (hadith/HadithReference).
 * Side by side (English left, Arabic right, as sunnah.com sets them) unless the reader turned it
 * off; a book in two columns, or a phone, stacks them.
 * `onNarrator` opens one narrator's full page; `onHadith` opens a sibling narration of the same number.
 */
import { useState } from 'react'

import { useHadithCollections } from '../../lib/hadith/useHadithCollections'
import { useHadithFavorites } from '../../lib/hadith/useHadithFavorites'
import { useKin, useNarrators, useWeakNotes } from '../../lib/hadith/useNarrators'
import { useHideChain } from '../../lib/hadith/useHideChain'
import { useSideBySide } from '../../lib/hadith/useSideBySide'
import { drawnChain } from '../../lib/hadith/rijal'
import { weakLinks, weakPoints } from '../../lib/hadith/weak'

import ChainSheet from './ChainSheet'
import Chip from '../ui/Chip'
import CopyButton from '../ui/CopyButton'
import FavoriteStar from './FavoriteStar'
import GradeMark from './GradeMark'
import HadithReference from './HadithReference'
import HadithText from '../ui/HadithText'
import NarrationFamily from './NarrationFamily'
import NarratorSheet from './NarratorSheet'
export default function HadithCards({ items, accent, collection, columns = false, onNarrator, onHadith }) {
  const [hideChain] = useHideChain()
  const { isFavorite, toggle } = useHadithFavorites()
  const { of } = useHadithCollections()
  const [sideBySide] = useSideBySide()
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
              split={sideBySide && !columns}
              names={names[ref]}
              onNarrator={setWho}
              footer={(
                <>
                  <HadithReference name={of(h.collection).name} number={h.number} part={h.part} book={h.book} inBook={h.in_book} cite={h.cite} />
                  {kin > 1 && (
                    <NarrationFamily
                      collection={h.collection} number={h.number} part={h.part} count={kin} accent={accent}
                      onOpen={(p) => onHadith?.({ collection: h.collection, book: p.book, number: h.number, part: p.part })}
                      onNarrator={setWho}
                    />
                  )}
                </>
              )}
              action={(
                <span className="flex flex-wrap items-center justify-end gap-2">
                  {!(collection && of(collection).sahih) && (
                    <GradeMark grades={h.grades} sahihBy={of(h.collection).sahih ? of(h.collection).name : null} cite={h.cite} />
                  )}
                  {(h.cut || rulings.length > 0) && (
                    <Chip quiet tinted accent={accent} onClick={() => setDrawn(h)}>
                      {h.cut ? (points > 0 ? `Chain · ${points} weak` : 'Chain') : 'Verdicts'}
                    </Chip>
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
