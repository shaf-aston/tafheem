/** Whether a media query matches now, kept current as the window changes. */
import { useSyncExternalStore } from 'react'

// The phone width the stylesheet's bottom bar goes by.
export const PHONE = '(max-width: 39.99rem)'

export function useMedia(query) {
  return useSyncExternalStore(
    (changed) => {
      const list = matchMedia(query)
      list.addEventListener('change', changed)
      return () => list.removeEventListener('change', changed)
    },
    () => matchMedia(query).matches,
    () => false,
  )
}
