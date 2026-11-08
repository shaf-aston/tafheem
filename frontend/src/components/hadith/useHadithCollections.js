/**
 * The hadith collections and one lookup by id, read from the cached query so
 * no component needs them passed down. `of(id)` always answers: an id the
 * list lacks reads as its own name, and `short` falls back to `name`.
 */
import { useQuery } from '@tanstack/react-query'

import { hadithCollectionsQuery } from '../../api'

export function useHadithCollections() {
  const { data: collections = [] } = useQuery(hadithCollectionsQuery)
  const of = (id) => {
    const c = collections.find((x) => x.id === id) ?? { id, name: id, sahih: false }
    return { ...c, short: c.short || c.name }
  }
  return { collections, of }
}

// The bookshelf's books (those with a shelf) as [[shelf, books]], in the order the collections list holds them.
export function shelvesOf(collections) {
  const shelves = new Map()
  for (const c of collections) if (c.shelf) shelves.set(c.shelf, [...(shelves.get(c.shelf) ?? []), c])
  return [...shelves]
}
