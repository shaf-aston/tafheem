/**
 * The books on this device, last opened first, each reopened at its page.
 * Says plainly where they live: clearing the browser's data clears them too.
 */
import { useEffect, useState } from 'react'

import knobs from '../../config/reader.json'

import SmallButton from '../ui/buttons/SmallButton'

export default function Library({ books, onOpen, onRemove }) {
  // Removing deletes the stored file, so it takes a second press; the first only asks.
  const [asking, setAsking] = useState(null)
  useEffect(() => {
    if (!asking) return
    const wait = setTimeout(() => setAsking(null), knobs['remove-confirm-ms'])
    return () => clearTimeout(wait)
  }, [asking])
  return (
    <section className="space-y-3" aria-label="Your books">
      <ul className="divide-y divide-[var(--border)] border-y border-[var(--border)]">
        {books.map((book) => (
          <li key={book.id} className="flex items-center gap-3 py-2">
            <button type="button" onClick={() => onOpen(book)} className="press tap flex-1 min-w-0 text-start py-1">
              <span className="block type-body text-[var(--text)] truncate">{book.name}</span>
              <span className="block type-small text-[var(--text-faint)]">Page {book.page}</span>
            </button>
            <SmallButton
              onClick={() => (asking === book.id ? onRemove(book) : setAsking(book.id))}
              aria-label={asking === book.id ? `Press again to remove ${book.name}` : `Remove ${book.name}`}
            >
              {asking === book.id ? 'Remove it?' : 'Remove'}
            </SmallButton>
          </li>
        ))}
      </ul>
      <p className="type-small text-[var(--text-faint)]">
        Kept on this device only. Clearing this browser's site data removes them.
      </p>
    </section>
  )
}
