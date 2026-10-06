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
 * family fold shows in a book, in search and in Starred alike.
 * `onNarrator` opens one narrator's full page; `onHadith` opens a sibling narration of the same number.
 */
import { useState } from 'react'

import { chainLinks, chainOf } from '../lib/hadithWords'
import { useHadithCollections } from '../lib/useHadithCollections'
import { useHadithFavorites } from '../lib/useHadithFavorites'
import { useNarrators } from '../lib/useNarrators'

import ChainSheet from './ui/ChainSheet'
import CopyButton from './ui/CopyButton'
import FavoriteStar from './ui/FavoriteStar'
import GradeMark from './ui/GradeMark'
import HadithText from './ui/HadithText'
import NarrationFamily from './ui/NarrationFamily'
import NarratorSheet from './ui/NarratorSheet'

export default function HadithCards({ items, accent, collection, columns = false, hideChain = false, onNarrator, onHadith }) {
  const { isFavorite, toggle } = useHadithFavorites()
  const { of } = useHadithCollections()
  const namesOf = useNarrators(items.map((h) => ({ collection: h.collection ?? collection, book: h.book })))
  // The hadith whose chain is drawn in the pop-up, if any.
  const [drawn, setDrawn] = useState(null)
  // The narrator whose sheet is open, if any.
  const [who, setWho] = useState(null)

  return (
    <>
      <ul className={`list-none m-0 p-0 ${columns ? 'grid gap-2 items-start md:grid-cols-2' : 'space-y-2'}`}>
        {items.map((item, i) => {
          const h = { ...item, collection: item.collection ?? collection }
          const ref = `${h.number}${h.part ?? ''}`
          const names = namesOf(h)
          // Narrations of this number with chains placed: the same digits, then letters only.
          const kin = h.part ? Object.keys(names).filter((k) => k.startsWith(`${h.number}`) && /^[a-z]+$/.test(k.slice(`${h.number}`.length))).length : 0
          return (
            <HadithText
              key={`${h.collection}:${ref}`}
              id={`hadith-${ref}`}
              index={i}
              label={collection ? ref : `${of(h.collection).short} ${ref}`}
              arabic={h.arabic}
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
                <span className="flex items-center gap-2">
                  {!(collection && of(collection).sahih) && (
                    <GradeMark grades={h.grades} sahihBy={of(h.collection).sahih ? of(h.collection).name : null} cite={h.cite} />
                  )}
                  {chainOf(h.arabic).chain && (
                    <button
                      type="button"
                      onClick={() => setDrawn(h)}
                      title="Draw the chain"
                      aria-label="Draw the chain"
                      className="press shrink-0 grid place-items-center text-[var(--text-faint)] hover:text-[var(--text-dim)] transition-colors"
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
          links={chainLinks(chainOf(drawn.arabic).chain)}
          author={of(drawn.collection).short}
          accent={accent}
          onClose={() => setDrawn(null)}
        />
      )}
    </>
  )
}
