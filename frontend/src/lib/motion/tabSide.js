/**
 * Which side a new tab comes in from: the side of the bar it was tapped on.
 *
 * `order` is the bar as the reader saw it (the phone's dock, or the desktop
 * strip). A tab not on it lives behind More, at the bar's far end. The bar can
 * reorder itself on the very switch it is drawing (the strip's recent tabs), so
 * the side is read off the order from the render BEFORE the switch, which is
 * the one the finger actually landed on.
 */
import { useState } from 'react'

const placeOf = (order, tab) => {
  const at = order.indexOf(tab)
  return at < 0 ? order.length : at
}

/** 'next' (came from the right), 'prev' (from the left) or null (no move, or both behind More). */
export function sideOf(order, from, to) {
  if (!from || from === to) return null
  const step = placeOf(order, to) - placeOf(order, from)
  return step > 0 ? 'next' : step < 0 ? 'prev' : null
}

export function useTabSide(tab, order) {
  const [seen, setSeen] = useState({ tab, order, side: null })
  if (seen.tab !== tab) {
    const side = sideOf(seen.order, seen.tab, tab)
    setSeen({ tab, order, side })
    return side
  }
  if (seen.order.join() !== order.join()) setSeen({ ...seen, order })
  return seen.side
}
