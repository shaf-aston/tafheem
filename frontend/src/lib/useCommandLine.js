/**
 * The typing half of a command surface: what was typed, what it means, which
 * row is under the cursor, and what each key does.
 *
 * The bar in the header and the orbit launcher share this, so Tab, the arrows
 * and Enter behave identically in both. Drawing is the only thing they do
 * differently.
 */
import { useCallback, useMemo, useState } from 'react'

import { classify, ghostFor } from './commandRoutes'

/**
 * `extras` is what a surface does with the keys the line itself has no use
 * for, so the whole "who handles which key" decision lives here instead of
 * being reassembled by every caller around the returned handler:
 *   onSpin(dir)  the horizontal arrows while no list is showing (the launcher
 *                turns its ring; the bar leaves the caret alone by omitting it)
 *   onEnter()    Enter while no list is showing
 *   onEscape()   Escape while the line is already empty; with text typed,
 *                Escape clears the line first. Omitted, Escape is left alone
 *                entirely (the launcher lets the dialog close natively).
 */
export function useCommandLine(tabs, onRun, extras = {}) {
  const { onSpin, onEnter, onEscape } = extras
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)

  const rows = useMemo(() => classify(query, tabs), [query, tabs])
  const ghost = useMemo(() => ghostFor(query, tabs), [query, tabs])

  const type = useCallback((text) => {
    setQuery(text)
    setActive(0)
  }, [])

  const run = useCallback((row) => {
    if (!row) return
    onRun(row)
    setQuery('')
    setActive(0)
  }, [onRun])

  /**
   * Returns true when it handled the key, so a caller can leave everything
   * else, Escape included, to whatever owns the surface.
   */
  const onKeyDown = useCallback((e) => {
    if (e.key === 'Tab' && ghost) {
      e.preventDefault()
      type(query + ghost)
      return true
    }
    // While a list is on screen the arrows belong to the list; spinning
    // whatever sits underneath would light one thing while Enter opened
    // another.
    if (onSpin && !rows.length
      && (e.key === 'ArrowRight' || e.key === 'ArrowLeft'
        || e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault()
      onSpin(e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : -1)
      return true
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (!rows.length) return false
      e.preventDefault()
      const step = e.key === 'ArrowDown' ? 1 : -1
      setActive((current) => (current + step + rows.length) % rows.length)
      return true
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      if (rows.length) run(rows[active])
      else if (onEnter) onEnter()
      return true
    }
    if (e.key === 'Escape' && onEscape) {
      e.preventDefault()
      if (query) type('')
      else onEscape()
      return true
    }
    return false
  }, [active, ghost, query, rows, run, type, onSpin, onEnter, onEscape])

  return { query, type, rows, active, setActive, ghost, onKeyDown, run }
}
