/** Whether a media query matches now, kept current as the window changes. */
import { useSyncExternalStore } from 'react'

import { themeVariable } from '../../theme'

// The phone width the stylesheet's bottom bar goes by.
export const PHONE = '(max-width: 39.99rem)'

// The least width, in px, the Terms tree is ever drawn whole at (theme.json layout terms-tree-min); the tree's own
// width at its smallest legible scale (lib/termsChart wholeWidth) raises it.
export const TERMS_TREE_MIN = Number(themeVariable('--layout-terms-tree-min'))
// The widest the page shell grows, in px (theme.json layout shell, in rem).
export const SHELL_MAX = parseFloat(themeVariable('--layout-shell')) * 16
export const atLeast = (px) => `(min-width: ${px}px)`

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
