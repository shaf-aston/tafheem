/**
 * A book world's file split for the page: a small index (areas, parts, each lesson's title and the ids of its questions)
 * and one file per part with the cards. Pure. Grow fetches the index when it opens and a part only when it is needed;
 * the authored book (public/grow/<book>.json) stays whole. Served by vite/growBooks.js in dev and written by it at build;
 * test/render.jsx answers the same paths in tests.
 */

/** Where a book's index and parts are served, from its authored file's path. */
export const indexPath = (source) => source.replace(/\.json$/, '/index.json')
export const partPath = (source, partId) => source.replace(/\.json$/, `/${partId}.json`)

/** The book with every lesson's cards replaced by `asks`, the ids of its question cards. */
export function indexOf(book) {
  const parts = book.parts.map(({ lessons, ...part }) => ({
    ...part,
    lessons: lessons.map(({ cards, ...lesson }) => ({ ...lesson, asks: cards.filter((card) => card.kind !== 'teach').map((card) => card.id) })),
  }))
  const { _comment, _cards, ...rest } = book
  return { ...rest, parts }
}

/** One part, cards and all; null for a part the book does not have. */
export const partOf = (book, partId) => book.parts.find((part) => part.id === partId) ?? null

/** A served path's answer for an authored book: its index, one of its parts, or null for anything else. */
export function servedFile(book, file) {
  if (file === 'index.json') return indexOf(book)
  return partOf(book, file.replace(/\.json$/, ''))
}
