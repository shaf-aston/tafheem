import { useCallback, useState } from 'react'

/**
 * One remembered choice, kept in localStorage between visits. Which commentary,
 * which quiz set, which Nahw view: remembered where it was chosen rather than
 * asked again. Panels remount when the tab strip moves, so without this a
 * choice does not survive a glance at another tab, let alone a reload.
 *
 * `allowed` is the ids currently on offer. Anything else falls back, so a book
 * since removed from the library cannot empty the panel; this also covers the
 * moment before a server-fed list lands, when the list is still empty.
 *
 * `fallback` defaults to the first id, which suits a list of books. A panel
 * whose default lives in config passes that instead of repeating it here.
 *
 * Omit `allowed` for a value that is not one of a list, a best score say, and
 * the stored string comes straight back.
 */
export function useRemembered(key, allowed = null, fallback = allowed?.[0] ?? '') {
  const [stored, setStored] = useState(() => {
    try { return localStorage.getItem(key) || '' } catch { return '' }
  })

  const choose = useCallback((value) => {
    setStored(value)
    try {
      localStorage.setItem(key, value)
    } catch {
      /* private browsing, the choice still holds for this session */
    }
  }, [key])

  const chosen = !allowed || allowed.includes(stored) ? stored : fallback
  return [chosen, choose]
}

/** The two things a remembered switch can be, written out rather than 1 and 0. */
const FLAG = ['on', 'off']

/**
 * A remembered switch, on the same store and with the same rules: what is saved
 * stays readable, and a value that is neither falls back like any other.
 */
export function useRememberedFlag(key, fallback) {
  const [saved, choose] = useRemembered(key, FLAG, fallback ? FLAG[0] : FLAG[1])
  const set = useCallback((on) => choose(on ? FLAG[0] : FLAG[1]), [choose])
  return [saved === FLAG[0], set]
}
