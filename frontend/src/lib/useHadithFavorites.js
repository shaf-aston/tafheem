import { useCallback, useSyncExternalStore } from 'react'

import { readSaved, writeSaved } from './stored'

/**
 * The hadiths a reader has starred, kept in this browser only.
 *
 * The hadith itself is stored, not just its id, so the Starred view can print
 * it without asking the backend. One store shared by every caller: the star in
 * a book, the star in a search hit and the Starred count must all agree the
 * moment one is pressed, which separate copies of the state would not.
 */
const KEY = 'hadith-favorites'

export const favoriteKey = ({ collection, number, part = '' }) => `${collection}:${number}${part}`

const read = () => {
  const saved = readSaved(KEY, [])
  return Array.isArray(saved) ? saved.filter((h) => h && typeof h === 'object') : []
}

let items = read()
const listeners = new Set()

const subscribe = (fn) => {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

function save(next) {
  items = next
  writeSaved(KEY, next)
  listeners.forEach((fn) => fn())
}

/** Star or unstar; a newly starred hadith goes first. Exported for the test. */
export function toggleFavorite(hadith) {
  const key = favoriteKey(hadith)
  const { collection, book, number, part = '', arabic, english = '', grades = [], cite = '' } = hadith
  save(items.some((h) => favoriteKey(h) === key)
    ? items.filter((h) => favoriteKey(h) !== key)
    : [{ collection, book, number, part, arabic, english, grades, cite }, ...items])
}

export function useHadithFavorites() {
  const favorites = useSyncExternalStore(subscribe, () => items)
  const isFavorite = useCallback((hadith) => favorites.some((h) => favoriteKey(h) === favoriteKey(hadith)), [favorites])
  return { favorites, isFavorite, toggle: toggleFavorite }
}
