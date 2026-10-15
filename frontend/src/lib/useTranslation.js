import { useQuery } from '@tanstack/react-query'

import { surahEditionQuery, translationsQuery } from '../api'
import { useRemembered } from './useRemembered'

// The first translation in backend/data/quran/editions.json, which is what the
// list would fall back to: asked for before the list lands, so the English
// comes with the Arabic instead of a round trip after it. A test holds the two
// in step; out of step it costs one wasted fetch, not a wrong book.
export const DEFAULT_TRANSLATION = 'saheeh-en'

const KEY = 'translation-edition'

/**
 * Which book to show. Before the list of books has come (`ids` null) the
 * reader's saved choice is trusted, so its fetch can start at once; after, a
 * book no longer installed falls back to the first one.
 */
export function editionFor(stored, ids) {
  if (!ids) return stored || DEFAULT_TRANSLATION
  return ids.includes(stored) ? stored : (ids[0] ?? '')
}

/**
 * The reader's chosen English translation, for a whole surah at once.
 *
 * Until now the only English in the app was one word under each Arabic word,
 * which reads as "The praise (be) to Allah Lord (of) the worlds". A translation
 * is a sentence. This is what puts one under every ayah.
 *
 * A surah at a time, not an ayah at a time, and the same query whether the
 * caller is drawing all 286 ayahs of al-Baqarah or the one being studied: both
 * then share one cached answer instead of asking twice for the same book.
 *
 * `textFor` returns nothing where the book has no line for that ayah, so a
 * caller can fall back to what it had rather than print a blank.
 */
export function useTranslation(surah) {
  const { data: list } = useQuery(translationsQuery)
  const books = list ?? []

  const [stored, choose] = useRemembered(KEY)
  const chosen = editionFor(stored, list?.map((book) => book.id))

  const { data, isError, error, refetch } = useQuery({
    ...surahEditionQuery(surah, chosen),
    enabled: Boolean(surah && chosen),
  })

  return {
    books,
    chosen,
    choose,
    // Whether this book's text for this surah is actually here. A caller must
    // not badge a line as coming from this book until it does: while the fetch
    // was in flight the caller was showing its old word-by-word gloss under the
    // new book's name, which is the app claiming a source for text that did not
    // come from it.
    ready: Boolean(data),
    isError,
    error,
    refetch,
    // The whole book, so a caller can badge the line it is drawing. The English
    // under an ayah is no longer the corpus's word-by-word gloss, so the badge
    // saying where it came from has to change with it.
    book: books.find((one) => one.id === chosen),
    textFor: (ayah) => data?.ayahs?.[ayah] || '',
  }
}
