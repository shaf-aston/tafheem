import { useCallback, useState } from 'react'

import { RECENT_KEPT } from './session'
import { forgetKey, progressKey, readSaved, writeSaved } from './stored'

/**
 * Persistent lookup history backed by localStorage. Kept under progressKey, so
 * Start over forgets every list by the one rule, with no list of names to update.
 * Items are stored newest-first; duplicates are deduplicated by JSON equality.
 *
 * How many are kept is one number in session.json, not a count per tab: three
 * tabs each passed their own and the Dictionary quietly kept twice what the
 * others did, which nobody chose.
 *
 * @param {string} name  - the list's name, e.g. 'dict-history'
 * @param {number} max   - max items to keep
 */
export function useHistory(name, max = RECENT_KEPT) {
  const key = progressKey(name)
  const [history, setHistory] = useState(() => readSaved(key, []))

  const push = useCallback((item) => {
    setHistory((prev) => {
      const serial = JSON.stringify(item)
      const next = [item, ...prev.filter((x) => JSON.stringify(x) !== serial)].slice(0, max)
      writeSaved(key, next)
      return next
    })
  }, [key, max])

  const clear = useCallback(() => {
    forgetKey(key)
    setHistory([])
  }, [key])

  return { history, push, clear }
}
