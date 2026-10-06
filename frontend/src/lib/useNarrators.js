/**
 * Narrators from rijal.db: the ones named in one book's Arabic, and the ones a search matches.
 *
 * For a run of hadiths from any books, a lookup from one hadith to its book's
 * names, by hadith ("1620a") to [start, end, id] slices. One request per book.
 * Empty until it arrives, for a hadith with no book, and when rijal.db is not
 * built or the read fails: a hadith is readable without its tappable names.
 */
import { useQueries, useQuery } from '@tanstack/react-query'

import { rijalChainsQuery, rijalSearchQuery } from '../api'

const NONE = {}

export function useNarrators(hadiths) {
  const books = [...new Set(hadiths.filter((h) => h.book != null).map((h) => `${h.collection}/${h.book}`))]
  const found = useQueries({ queries: books.map((b) => rijalChainsQuery(...b.split('/'))) })
  const byBook = Object.fromEntries(books.map((b, i) => [b, found[i].data?.ready ? found[i].data.chains : NONE]))
  return (h) => byBook[`${h.collection}/${h.book}`] ?? NONE
}

/** Narrators whose name starts with what was searched; none when rijal.db is not built or nothing matches. */
export function useNarratorMatches(q) {
  const { data } = useQuery({ ...rijalSearchQuery(q), enabled: Boolean(q) })
  return data?.ready ? data.narrators : []
}
