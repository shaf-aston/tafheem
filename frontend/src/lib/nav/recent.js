/**
 * The tab strip, and which tabs stay alive. App sees only useStrip and keepRecent.
 *
 * The strip's tabs keep their places: the fixed tabs, then the seed's, always in the same order, so a
 * tab is always where it was and keeps its number key. It used to swap the oldest seed tab out for each
 * new one opened, so one place showed Daleel on one screen and Quiz on the next. A tab off the strip
 * that is open shows after them while it is open, so the strip still says where you are.
 */
import { useMemo } from 'react'

/** The strip for `active`: the fixed tabs, then the seed's, then `active` if it is listed and not among them. */
export function stripOf(tabs, fixed, seed, active) {
  const ids = [...fixed, ...seed]
  if (tabs.some((t) => t.id === active) && !ids.includes(active)) ids.push(active)
  return ids.map((id) => tabs.find((t) => t.id === id))
}

export function useStrip(tabs, fixed, seed, active) {
  return useMemo(() => stripOf(tabs, fixed, seed, active), [tabs, fixed, seed, active])
}

/** The tabs kept alive: `id` last, the oldest dropped past `max`. Pure, so it can be tested. */
export const keepRecent = (alive, id, max) => [...alive.filter((t) => t !== id), id].slice(-max)
