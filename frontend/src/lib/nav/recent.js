/**
 * Recent tabs: the strip's places after the fixed tabs. `{ slots, next }`:
 * the tabs in place, and which slot the next new tab takes. Opening a tab not
 * on the strip puts it in that slot and moves `next` on, so the oldest arrival
 * goes, as before, but every other tab keeps its place, and its number key.
 * App sees only useStrip.
 */
import { useEffect, useMemo } from 'react'
import { progressKey } from '../store/stored'
import { useRemembered } from '../store/useRemembered'

/** The fixed tabs, then the recent ones. Strip order = number keys. */
export const stripOf = (tabs, fixed, recent) => [...fixed, ...recent.slots].map((id) => tabs.find((t) => t.id === id))

/** The strip before anything is opened: the seed in its slots. */
export const seedOf = (seed) => ({ slots: seed, next: 0 })

/** Opening `id`: unchanged if it already shows or is a hidden tab (not in `tabs`), else it takes slot `next`. */
export function addRecent(recent, id, tabs, fixed) {
  if (!tabs.some((t) => t.id === id) || [...fixed, ...recent.slots].includes(id)) return recent
  const slots = recent.slots.map((one, at) => (at === recent.next ? id : one))
  return { slots, next: (recent.next + 1) % slots.length }
}

/** Saved text back to the strip; anything broken or stale starts again from `seed`. */
export function readRecent(text, tabs, fixed, seed) {
  try {
    const saved = JSON.parse(text)
    // An older save is the bare list; its oldest was first, so the next new tab takes slot 0.
    const { slots, next = 0 } = Array.isArray(saved) ? { slots: saved } : saved
    const ids = [...fixed, ...slots] // one Set: no repeats, and no fixed tab among the recent
    if (slots.length === seed.length && Number.isInteger(next) && next >= 0 && next < slots.length
      && new Set(ids).size === ids.length && slots.every((id) => tabs.some((t) => t.id === id))) return { slots, next }
  } catch {
    /* nothing saved yet */
  }
  return seedOf(seed)
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

/** The tabs kept alive: `id` last, the oldest dropped past `max`. Pure, so it can be tested. */
export const keepRecent = (alive, id, max) => [...alive.filter((t) => t !== id), id].slice(-max)
