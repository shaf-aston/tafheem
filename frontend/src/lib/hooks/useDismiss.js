/** Calls onDismiss(event) on Escape and on a press outside `ref` (one ref, or a list: inside any is inside). */
import { useEffect } from 'react'

export function useDismiss(ref, onDismiss, { outside = true, escape = true, enabled = true } = {}) {
  useEffect(() => {
    if (!enabled) return undefined
    const onPress = (event) => {
      if (![ref].flat().some((one) => one?.current?.contains(event.target))) onDismiss(event)
    }
    const onKey = (event) => { if (event.key === 'Escape') onDismiss(event) }
    if (outside) document.addEventListener('pointerdown', onPress)
    if (escape) document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPress)
      document.removeEventListener('keydown', onKey)
    }
  }, [ref, onDismiss, outside, escape, enabled])
}
