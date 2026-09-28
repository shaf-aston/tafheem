import { useCallback, useSyncExternalStore } from 'react'

/**
 * The hadiths a reader has starred, kept in this browser only.
 *
 * The hadith itself is stored, not just its id, so the Starred view can print
 * it without asking the backend. One store shared by every caller: the star in
 * a book, the star in a search hit and the Starred count must all agree the
 * moment one is pressed, which separate copies of the state would not.
 */
const KEY = 'hadith-favorites'

export const keyOf = ({ collection, number, part = '' }) => `${collection}:${number}${part}`

const read = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || '[]')
    return Array.isArray(saved) ? saved.filter((h) => h && typeof h === 'object') : []
  } catch {
    return []
  }
}

let items = read()
const listeners = new Set()

const subscribe = (fn) => {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

function save(next) {
  items = next
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    /* private browsing, the star still works for this session */
  }
  listeners.forEach((fn) => fn())
}

/** Star or unstar; a newly starred hadith goes first. Exported for the test. */
export function toggleFavorite(hadith) {
  const key = keyOf(hadith)
  const { collection, number, part = '', arabic, english = '' } = hadith
  save(items.some((h) => keyOf(h) === key)
    ? items.filter((h) => keyOf(h) !== key)
    : [{ collection, number, part, arabic, english }, ...items])
}

export function useHadithFavorites() {
  const favorites = useSyncExternalStore(subscribe, () => items)
  const isFavorite = useCallback((hadith) => favorites.some((h) => keyOf(h) === keyOf(hadith)), [favorites])
  return { favorites, isFavorite, toggle: toggleFavorite }
}
