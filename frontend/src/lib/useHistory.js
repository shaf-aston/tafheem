import { useCallback, useState } from 'react'

import { RECENT_KEPT } from './session'

/**
 * Persistent lookup history backed by localStorage.
 * Items are stored newest-first; duplicates are deduplicated by JSON equality.
 *
 * How many are kept is one number in session.json, not a count per tab: three
 * tabs each passed their own and the Dictionary quietly kept twice what the
 * others did, which nobody chose.
 *
 * @param {string} key   - localStorage key
 * @param {number} max   - max items to keep
 */
export function useHistory(key, max = RECENT_KEPT) {
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(key) || '[]') } catch { return [] }
  })

  const push = useCallback((item) => {
    setHistory((prev) => {
      const serial = JSON.stringify(item)
      const next = [item, ...prev.filter((x) => JSON.stringify(x) !== serial)].slice(0, max)
      try {
        localStorage.setItem(key, JSON.stringify(next))
      } catch {
        /* private browsing, history still works for this session */
      }
      return next
    })
  }, [key, max])

  const clear = useCallback(() => {
    try {
      localStorage.removeItem(key)
    } catch {
      /* nothing stored to remove */
    }
    setHistory([])
  }, [key])

  return { history, push, clear }
}
