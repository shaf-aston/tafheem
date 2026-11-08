/**
 * Which collection is open: the six books as spines standing on a shelf, each
 * name written down its own spine. The open one tips out towards the reader.
 * Absent while only one is indexed rather than shown as a one-choice control.
 *
 * A shelf rather than a row of tabs because these are books, and because six
 * spines fit a phone's width where six worded tabs wrapped onto two rows and
 * the second read as a different control. A narrow screen scrolls the shelf
 * sideways rather than wrapping it (.shelf in components.css).
 *
 * The further books (Mishkat and the rest, those with a `shelf`) stand in the
 * bookshelf at the shelf's end instead, so the six stay the first thing seen:
 * the bookshelf opens them all (onBookshelf), and one of them, while open, stands
 * beside it so the shelf still shows which book this is.
 */
import { useHadithCollections } from '../useHadithCollections'

export default function HadithCollectionPicker({ value, onChange, accent, onBookshelf, bookshelfOpen = false }) {
  const { collections, of } = useHadithCollections()
  if (collections.length <= 1) return null
  const shown = collections.filter((c) => !c.shelf || (c.id === value && !bookshelfOpen))
  const further = collections.some((c) => c.shelf)

  return (
    <div role="group" aria-label="Collection" className="shelf" style={{ '--c': accent }}>
      {shown.map((c) => (
        <button
          key={c.id}
          type="button"
          aria-pressed={c.id === value && !bookshelfOpen}
          title={c.name}
          onClick={() => onChange(c.id)}
          className="shelf-spine"
          data-sahih={c.sahih || undefined}
        >
          <span>{of(c.id).short}</span>
        </button>
      ))}
      {further && onBookshelf && (
        <button type="button" aria-pressed={bookshelfOpen} title="More books of hadith" onClick={onBookshelf} className="shelf-more">
          <svg viewBox="0 0 36 44" aria-hidden="true">
            <path d="M2 1h32v42M2 1v42M2 15h32M2 29h32M2 43h32" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="M6 5h3v10H6zM10 7h3v8h-3zM14 4h3v11h-3zM22 6l3-1 3 10-3 1zM7 19h3v10H7zM11 21h4v8h-4zM18 18h3v11h-3zM22 20h3v9h-3zM26 19h3v10h-3zM6 33h3v10H6zM10 35h3v8h-3zM17 34h4v9h-4zM24 32h3v11h-3z" fill="currentColor" opacity="0.6" />
          </svg>
          <span>More books</span>
        </button>
      )}
    </div>
  )
}
