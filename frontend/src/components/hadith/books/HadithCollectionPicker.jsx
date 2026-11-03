/**
 * Which collection is open: the six books as spines standing on a shelf, each
 * name written down its own spine. The open one tips out towards the reader.
 * Absent while only one is indexed rather than shown as a one-choice control.
 *
 * A shelf rather than a row of tabs because these are books, and because six
 * spines fit a phone's width where six worded tabs wrapped onto two rows and
 * the second read as a different control. A narrow screen scrolls the shelf
 * sideways rather than wrapping it (.shelf in components.css).
 */
import { useHadithCollections } from '../useHadithCollections'

export default function HadithCollectionPicker({ value, onChange, accent }) {
  const { collections, of } = useHadithCollections()
  if (collections.length <= 1) return null

  return (
    <div role="group" aria-label="Collection" className="shelf" style={{ '--c': accent }}>
      {collections.map((c) => (
        <button
          key={c.id}
          type="button"
          aria-pressed={c.id === value}
          title={c.name}
          onClick={() => onChange(c.id)}
          className="shelf-spine"
          data-sahih={c.sahih || undefined}
        >
          <span>{of(c.id).short}</span>
        </button>
      ))}
    </div>
  )
}
