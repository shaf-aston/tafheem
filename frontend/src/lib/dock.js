/**
 * The phone's bar: the tabs kept one tap away, a list of tab ids in bar order.
 * Everything else lives under More. Saved as plain text, "quran,dict,grow,quiz",
 * which is the whole format: the order is the array, and a tab not in it is in More.
 *
 * Like lib/recent.js for the desktop strip, this file owns the rule and the rest
 * of the app only draws the list it hands back.
 */
import { useCallback, useMemo } from 'react'
import { useRemembered } from './useRemembered'

const DOCK_KEY = 'dock-tabs'

/** Saved text back to the list: tabs that no longer exist and repeats are dropped, and an empty result starts again from `seed`. */
export function readDock(text, tabs, seed) {
  const ids = String(text ?? '').split(',').filter((id) => tabs.some((tab) => tab.id === id))
  const kept = [...new Set(ids)].slice(0, seed.length)
  return kept.length ? kept : seed
}

/**
 * Put `id` in bar slot `to`, or send it to More when `to` is null. Dropping a
 * More tab on a full bar replaces whatever sat in that slot, which goes to
 * More; moving one already on the bar reorders. The bar never holds fewer than one.
 */
export function moveDock(dock, id, to, size) {
  const rest = dock.filter((one) => one !== id)
  if (to === null) return rest.length ? rest : dock
  const full = rest.length >= size
  rest.splice(Math.min(to, rest.length), full ? 1 : 0, id)
  return rest
}

/** The bar for `seed`'s size, remembered between visits, and the one way to change it. */
export function useDock(tabs, seed) {
  const [saved, save] = useRemembered(DOCK_KEY)
  const dock = useMemo(() => readDock(saved, tabs, seed), [saved, tabs, seed])
  const place = useCallback((id, to) => save(moveDock(dock, id, to, seed.length).join(',')), [dock, seed, save])
  return [dock, place]
}
