/**
 * Where the Hadith tab is: "bukhari", "bukhari/1", or "bukhari/1/2a" for one
 * hadith. Same shape as lib/timelineLayout's parsePlace/placeOf, so a deep
 * link and the back arrow work here exactly as they do on every other tab.
 *
 * Pure: no fetching. Only the collection id is checked against what was
 * loaded; a book or hadith number that does not exist is left to the request
 * that follows, the same way a stale Daleel book filter is.
 */
const HADITH_REF = /^(\d+)([a-z]?)$/

export function parsePlace(q, collections) {
  if (!q) return null
  const [collectionId, book, hadith, ...rest] = q.split('/')
  if (rest.length || !collections.some((c) => c.id === collectionId)) return null
  if (book === undefined) return { collection: collectionId, book: null, number: null, part: '' }
  if (!/^\d+$/.test(book)) return null
  if (hadith === undefined) return { collection: collectionId, book: Number(book), number: null, part: '' }
  const match = HADITH_REF.exec(hadith)
  if (!match) return null
  return { collection: collectionId, book: Number(book), number: Number(match[1]), part: match[2] }
}

// The (collection, book) a place string names, before the collections are known to check it; null if none.
export function bookOf(q) {
  const [collection, book] = (q ?? '').split('/')
  return /^\d+$/.test(book ?? '') ? [collection, Number(book)] : null
}

export const placeOf = (collection, book, number, part = '') => (
  number != null ? `${collection}/${book}/${number}${part}` : book != null ? `${collection}/${book}` : collection
)
