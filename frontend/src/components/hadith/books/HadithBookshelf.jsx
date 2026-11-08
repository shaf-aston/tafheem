/**
 * The bookshelf: the further books of hadith, beyond the six on the tab's own
 * shelf (HadithCollectionPicker), drawn as a wooden bookshelf. Each kind of book
 * ("Gathered by topic", "Forty hadith") stands on its own plank, cover out, its
 * Arabic title across the cover and beside it only its name and hadith count,
 * never taller than the cover; picking it opens it like any collection.
 *
 * It opens out of the "More books" tile that was pressed (lib/motion/openFrom):
 * the tile turns over and grows into the whole bookshelf while the page glides
 * down to it, so the reader is carried in, then its planks settle one by one.
 */
import { useLayoutEffect, useRef } from 'react'

import { shelvesOf, useHadithCollections } from '../useHadithCollections'
import { holdGlideUnderHeader } from '../../../lib/motion/scrollToEl'
import { openFrom } from '../../../lib/motion/openFrom'

import ArabicText from '../../ui/text/ArabicText'
import EmptyState from '../../ui/feedback/EmptyState'

function Plank({ shelf, books, index, onPick }) {
  return (
    <section aria-label={shelf} className="bookshelf-shelf rise-in" style={{ '--i': index + 1 }}>
      <h3 className="eyebrow">{shelf}</h3>
      <ul className="bookshelf-row">
        {books.map((b) => (
          <li key={b.id}>
            <button type="button" onClick={() => onPick(b.id)} className="bookshelf-book group"
              aria-label={b.count > 0 ? `${b.name}, ${b.count.toLocaleString()} hadiths` : b.name}>
              <span className="bookshelf-cover" aria-hidden="true">
                <ArabicText>{b.arabic || b.short || b.name}</ArabicText>
              </span>
              <span className="bookshelf-words">
                <span className="type-ui font-semibold text-[var(--text)] group-hover:text-[var(--c)] transition-colors">{/* No break at a hyphen: "an-" alone at a line's end. */}{b.name.replaceAll('-', '\u2011')}</span>
                {b.count > 0 && <span className="type-small tabular-nums text-[var(--text-dim)]">{b.count.toLocaleString()} hadiths</span>}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function HadithBookshelf({ onPick, accent }) {
  const { collections } = useHadithCollections()
  const shelves = shelvesOf(collections)
  const bookshelf = useRef(null)
  // Once the books are in (the section is absent while there are none), not on every render.
  const stocked = shelves.length > 0
  useLayoutEffect(() => {
    if (!bookshelf.current) return undefined
    openFrom(bookshelf.current, document.querySelector('.shelf-more'))
    return holdGlideUnderHeader(bookshelf.current)
  }, [stocked])
  if (!stocked) return <EmptyState>No further book is on the bookshelf yet.</EmptyState>

  return (
    <section ref={bookshelf} aria-label="Bookshelf" className="bookshelf" style={{ '--c': accent }}>
      <div className="bookshelf-frame">
        {shelves.map(([shelf, books], i) => (
          <Plank key={shelf} shelf={shelf} books={books} index={i} onPick={onPick} />
        ))}
      </div>
    </section>
  )
}
