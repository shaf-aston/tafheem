/** Whether a media query matches now, kept current as the window changes. */
import { useSyncExternalStore } from 'react'

import { themeVariable } from '../theme'

// The phone width the stylesheet's bottom bar goes by.
export const PHONE = '(max-width: 39.99rem)'

// The width from which the Terms tree is drawn whole (theme.json layout terms-tree-min).
export const TERMS_TREE = `(min-width: ${themeVariable('--layout-terms-tree-min')}px)`

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
