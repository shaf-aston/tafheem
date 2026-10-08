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
const NO_WEAK = { notes: [], links: [], rulings: [], rules: null, scale: [] }

/** Each book's chains reply as `(hadith) => reply`, once per book; undefined until it arrives or while rijal.db is not built. */
function useChains(hadiths) {
  const books = [...new Set(hadiths.filter((h) => h.book != null).map((h) => `${h.collection}/${h.book}`))]
  const found = useQueries({ queries: books.map((b) => rijalChainsQuery(...b.split('/'))) })
  const byBook = Object.fromEntries(books.map((b, i) => [b, found[i].data?.ready ? found[i].data : undefined]))
  return (h) => byBook[`${h.collection}/${h.book}`]
}

export function useNarrators(hadiths) {
  const chainsOf = useChains(hadiths)
  return (h) => chainsOf(h)?.chains ?? NONE
}

/**
 * The weak narrators of a hadith ("1620a" is its key in the book), the links of
 * its chain a source puts in doubt (`links`, with `rules`: what each kind says,
 * quoted), what classical books say of it (`rulings`) and the twelve levels the narrators sit on:
 * `(hadith, ref) => {notes, links, rulings, rules, scale}`. Same request as
 * useNarrators. All empty when usul.db is not built, and the hadith reads as it
 * did before weak points.
 */
export function useWeakNotes(hadiths) {
  const chainsOf = useChains(hadiths)
  return (h, ref) => {
    const found = chainsOf(h)
    const notes = found?.notes?.[ref] ?? []
    const links = found?.links?.[ref] ?? []
    const rulings = found?.rulings?.[ref] ?? []
    return notes.length || links.length || rulings.length ? { notes, links, rulings, rules: found.link_rules, scale: found.scale } : NO_WEAK
  }
}

/** Narrators whose name starts with what was searched; none when rijal.db is not built or nothing matches. */
export function useNarratorMatches(q) {
  const { data } = useQuery({ ...rijalSearchQuery(q), enabled: Boolean(q) })
  return data?.ready ? data.narrators : []
}
