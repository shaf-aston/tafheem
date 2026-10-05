/**
 * Narrators from rijal.db: the ones named in one book's Arabic, and the ones a search matches.
 *
 * The narrators named in one book's Arabic, by hadith ("1620a") to
 * [start, end, id] slices. Empty until it arrives, and when rijal.db is not
 * built or the read fails: a book is readable without its tappable names.
 */
import { useQuery } from '@tanstack/react-query'

import { rijalChainsQuery, rijalSearchQuery } from '../api'

const NONE = {}

export function useNarrators(collection, book) {
  const { data } = useQuery(rijalChainsQuery(collection, book))
  return data?.ready ? data.chains : NONE
}

/** Narrators whose name starts with what was searched; none when rijal.db is not built or nothing matches. */
export function useNarratorMatches(q) {
  const { data } = useQuery({ ...rijalSearchQuery(q), enabled: Boolean(q) })
  return data?.ready ? data.narrators : []
}
