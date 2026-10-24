/**
 * The classical books on a root, in the order the switch shows them.
 *
 * Ibn Faris always, since his card is what says the book is missing or has no
 * entry; the others only when the backend sent an entry for them, so the
 * switch never offers a book with nothing in it. Order and short names are
 * dictionary.json's, not this file's.
 */
import { useQuery } from '@tanstack/react-query'

import { getLexicons } from '../api'
import config from '../config/dictionary.json'

export const MAQAYEES = 'maqayees'

const LISTED = config.classical.books

/** [{ id, label }] for Ibn Faris and every book in `entries` (the lexicons answer). */
export function classicalBooks(entries = []) {
  const sent = new Map(entries.map((entry) => [entry.book, entry]))
  const listed = LISTED.filter((book) => book.id === MAQAYEES || sent.has(book.id))
  const unlisted = entries
    .filter((entry) => !LISTED.some((book) => book.id === entry.book))
    .map((entry) => ({ id: entry.book, label: entry.title }))
  return [...listed, ...unlisted]
}

/** The books' entries on a root. One query, read by the shelf and by the switch above it. */
export const useLexicons = (root) => useQuery({
  queryKey: ['lexicons', root],
  queryFn: () => getLexicons(root),
  enabled: Boolean(root),
})
