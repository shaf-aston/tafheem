import { useCallback, useState } from 'react'

/**
 * Which hadiths a reader has starred, kept in this browser only.
 *
 * No backend: tafheem has nowhere else that remembers one reader's own
 * choices, so this stays local rather than inventing a second storage model
 * for one small feature. Shaped like lib/useHistory: a plain array behind
 * localStorage, read once and written on every change.
 */
const KEY = 'hadith-favorites'

const keyOf = ({ collection, number, part = '' }) => `${collection}:${number}${part}`

export function useHadithFavorites() {
  const [favorites, setFavorites] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]') } catch { return [] }
  })

  const isFavorite = useCallback((hadith) => favorites.includes(keyOf(hadith)), [favorites])

  const toggle = useCallback((hadith) => {
    const key = keyOf(hadith)
    setFavorites((prev) => {
      const next = prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
      try {
        localStorage.setItem(KEY, JSON.stringify(next))
      } catch {
        /* private browsing, the star still works for this session */
      }
      return next
    })
  }, [])

  return { isFavorite, toggle }
}
