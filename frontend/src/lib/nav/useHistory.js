import { useCallback } from 'react'

import { RECENT_KEPT } from './session'
import { forgetKey, progressKey, readSaved, useStoredSaved, writeSaved } from '../store/stored'

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
  const history = useStoredSaved(key, [])

  const push = useCallback((item) => {
    const serial = JSON.stringify(item)
    writeSaved(key, [item, ...readSaved(key, []).filter((x) => JSON.stringify(x) !== serial)].slice(0, max))
  }, [key, max])

  const clear = useCallback(() => forgetKey(key), [key])

  return { history, push, clear }
}
