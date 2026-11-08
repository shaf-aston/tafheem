/**
 * The bookshelf: the further books of hadith, beyond the six on the tab's own
 * shelf (HadithCollectionPicker), drawn as a wooden bookshelf. Each kind of book
 * ("Gathered by topic", "Forty hadith") stands on its own plank, spines out, the
 * Arabic title running down each spine. Pointing at or focusing a spine reads its
 * name, who gathered it, one line about it and its hadith count on the plaque
 * under the plank; picking it opens it like any collection.
 *
 * It opens out of the "More books" tile that was pressed (lib/motion/openFrom):
 * the tile turns over and grows into the whole bookshelf while the page glides
 * down to it, so the reader is carried in, then its planks settle one by one.
 */
import { useLayoutEffect, useRef, useState } from 'react'

import { shelvesOf, useHadithCollections } from '../useHadithCollections'
import { holdGlideUnderHeader } from '../../../lib/motion/scrollToEl'
import { openFrom } from '../../../lib/motion/openFrom'

import ArabicText from '../../ui/text/ArabicText'
import EmptyState from '../../ui/feedback/EmptyState'

function Plank({ shelf, books, index, onPick }) {
  const [leaning, setLeaning] = useState(books[0].id)
  const book = books.find((b) => b.id === leaning)
  return (
    <section aria-label={shelf} className="bookshelf-shelf rise-in" style={{ '--i': index + 1 }}>
      <h3 className="eyebrow">{shelf}</h3>
      <ul className="bookshelf-row">
        {books.map((b) => (
          <li key={b.id}>
            <button
              type="button"
              aria-label={b.name}
              onClick={() => onPick(b.id)}
              onPointerEnter={() => setLeaning(b.id)}
              onFocus={() => setLeaning(b.id)}
              className="bookshelf-book"
              data-leaning={b.id === leaning || undefined}
            >
              <ArabicText size="sm">{b.arabic || b.short || b.name}</ArabicText>
            </button>
          </li>
        ))}
      </ul>
      <div className="bookshelf-plaque">
        <span className="type-ui font-semibold text-[var(--text)]">{book.name}</span>
        {book.by && <span className="type-small text-[var(--text-dim)]">{book.by}</span>}
        {book.about && <span className="type-small text-[var(--text-dim)]">{book.about}</span>}
        {book.count > 0 && <span className="type-small tabular-nums text-[var(--text-faint)]">{book.count.toLocaleString()} hadiths</span>}
      </div>
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
      <p className="type-ui text-[var(--text-dim)]">More books of hadith, beyond the six. Pick one to open it.</p>
      <div className="bookshelf-frame">
        {shelves.map(([shelf, books], i) => (
          <Plank key={shelf} shelf={shelf} books={books} index={i} onPick={onPick} />
        ))}
      </div>
    </section>
  )
}
