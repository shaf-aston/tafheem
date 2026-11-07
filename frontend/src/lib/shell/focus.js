/**
 * Focus mode: while a lesson runs, the app's own bars step aside so the
 * question has the whole screen (the header and the phone's tab bar hide,
 * styles/components.css `[data-focus]`). The lesson's own ✕ is the way out.
 *
 * One flag on <html>, counted, so two runners mounted at once (a hidden tab
 * kept alive and the one showing) cannot switch it off under each other.
 */
import { useEffect } from 'react'

let holders = 0

function set(on) {
  holders = Math.max(0, holders + (on ? 1 : -1))
  if (holders) document.documentElement.dataset.focus = 'lesson'
  else delete document.documentElement.dataset.focus
}

/** Hold focus mode while `on` is true and the calling component is mounted. */
export function useFocusMode(on) {
  useEffect(() => {
    if (!on) return undefined
    set(true)
    return () => set(false)
  }, [on])
}
