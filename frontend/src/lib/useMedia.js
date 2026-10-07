/** Whether a media query matches now, kept current as the window changes. */
import { useSyncExternalStore } from 'react'

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
