/**
 * The pinned app header's height: one writer (App, as the header wraps), any reader.
 *
 * CSS reads it as --app-header-h. Script that needs the number (an observer's
 * margin, so "scrolled away" means "gone under the header") reads it here, and
 * hears when it changes: a value read once went stale when the header rewrapped
 * on a resize or a phone turning round.
 */
import { useSyncExternalStore } from 'react'

let height = 0
const listeners = new Set()

export function setHeaderHeight(px) {
  if (px === height) return
  height = px
  globalThis.document?.documentElement.style.setProperty('--app-header-h', `${px}px`)
  listeners.forEach((listener) => listener())
}

export const useHeaderHeight = () => useSyncExternalStore(
  (listener) => {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
  () => height,
  () => 0,
)
