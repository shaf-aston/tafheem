/**
 * Recent tabs: the strip's places after the fixed tabs. A list, oldest first.
 * Opening a tab not on the strip drops the oldest and adds it at the end, so
 * the strip never grows. App sees only useStrip.
 */
import { useEffect, useMemo } from 'react'
import { progressKey } from './stored'
import { useRemembered } from './useRemembered'

/** The fixed tabs, then the recent ones. Strip order = number keys. */
export const stripOf = (tabs, fixed, recent) => [...fixed, ...recent].map((id) => tabs.find((t) => t.id === id))

/** Opening `id`: unchanged if it already shows or is a hidden tab (not in `tabs`), else the oldest goes and it comes in at the end. */
export const addRecent = (recent, id, tabs, fixed) =>
  !tabs.some((t) => t.id === id) || [...fixed, ...recent].includes(id) ? recent : [...recent.slice(1), id]

/** Saved text back to the list; anything broken or stale starts again from `seed`. */
export function readRecent(text, tabs, fixed, seed) {
  try {
    const recent = JSON.parse(text)
    const ids = [...fixed, ...recent]  // one Set: no repeats, and no fixed tab among the recent
    if (recent.length === seed.length && new Set(ids).size === ids.length && recent.every((id) => tabs.some((t) => t.id === id))) return recent
  } catch {
    /* nothing saved yet */
  }
  return seed
}

/** The strip for `active`, remembered between visits. Every way into a tab passes here. */
export function useStrip(tabs, fixed, seed, active) {
  const [saved, save] = useRemembered(progressKey('recent-tabs'))
  const recent = useMemo(() => readRecent(saved, tabs, fixed, seed), [saved, tabs, fixed, seed])
  useEffect(() => {
    const next = addRecent(recent, active, tabs, fixed)
    if (next !== recent) save(JSON.stringify(next))
  }, [recent, active, tabs, fixed, save])
  return useMemo(() => stripOf(tabs, fixed, recent), [tabs, fixed, recent])
}
