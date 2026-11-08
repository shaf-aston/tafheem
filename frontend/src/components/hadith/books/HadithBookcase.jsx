/**
 * The bookcase: the further books of hadith, beyond the six on the tab's own
 * shelf (HadithCollectionPicker), one shelf of the case per kind of book
 * ("Gathered by topic", "Forty hadith"), read top to bottom. Each book shows
 * its cover (its Arabic title) and beside it who gathered it, one line about it
 * and how many hadiths it holds; picking it opens it like any collection.
 *
 * It opens out of the "More books" tile that was pressed (lib/motion/openFrom):
 * the tile turns over and grows into the whole case while the page glides down to
 * it, so the reader is carried into the case, then its shelves settle one by one.
 */
import { useLayoutEffect, useRef } from 'react'

import { shelvesOf, useHadithCollections } from '../useHadithCollections'
import { holdGlideUnderHeader } from '../../../lib/motion/scrollToEl'
import { openFrom } from '../../../lib/motion/openFrom'

import ArabicText from '../../ui/text/ArabicText'
import EmptyState from '../../ui/feedback/EmptyState'

export default function HadithBookcase({ onPick, accent }) {
  const { collections } = useHadithCollections()
  const shelves = shelvesOf(collections)
  const bookcase = useRef(null)
  // Once the books are in (the section is absent while there are none), not on every render.
  const stocked = shelves.length > 0
  useLayoutEffect(() => {
    if (!bookcase.current) return undefined
    openFrom(bookcase.current, document.querySelector('.shelf-case'))
    return holdGlideUnderHeader(bookcase.current)
  }, [stocked])
  if (!stocked) return <EmptyState>No further book is on the bookcase yet.</EmptyState>

  return (
    <section ref={bookcase} aria-label="Bookcase" className="bookcase" style={{ '--c': accent }}>
      <p className="type-ui text-[var(--text-dim)]">More books of hadith, beyond the six. Pick one to open it.</p>
      {shelves.map(([shelf, books], i) => (
        <section key={shelf} aria-label={shelf} className="bookcase-shelf rise-in" style={{ '--i': i + 1 }}>
          <h3 className="eyebrow">{shelf}</h3>
          <ul className="bookcase-row">
            {books.map((book) => (
              <li key={book.id}>
                <button type="button" onClick={() => onPick(book.id)} className="bookcase-book lift press group">
                  <span className="bookcase-cover" aria-hidden="true">
                    <ArabicText size="sm">{book.arabic || book.short || book.name}</ArabicText>
                  </span>
                  <span className="min-w-0 flex flex-col gap-0.5 text-start">
                    <span className="type-ui font-semibold text-[var(--text)] group-hover:text-[var(--c)] transition-colors">{book.name}</span>
                    {book.by && <span className="type-small text-[var(--text-dim)]">{book.by}</span>}
                    {book.about && <span className="type-small text-[var(--text-dim)]">{book.about}</span>}
                    {book.count > 0 && <span className="type-small tabular-nums text-[var(--text-faint)]">{book.count.toLocaleString()} hadiths</span>}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </section>
  )
}
