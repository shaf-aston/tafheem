/**
 * Recent tabs: the strip's last places, after the fixed tabs (row 1, 2). A
 * list, oldest first. Opening a tab not on the strip drops the oldest and adds
 * it far right, so the strip never grows. App sees only useStrip.
 */
import { useEffect, useMemo } from 'react'
import { useRemembered } from './useRemembered'

const fixed = (tab) => tab.row < 3

// A half tab (Nahw, Sarf) is one recent tab together with its partner.
function withPartner(tabs, id) {
  const tab = tabs.find((t) => t.id === id)
  return tab.half ? tabs.filter((t) => t.half && t.group === tab.group) : [tab]
}

/** Fixed tabs in list order, then the recent ones. Strip order = number keys. */
export const stripOf = (tabs, recent) => [...tabs.filter(fixed), ...recent.flatMap((id) => withPartner(tabs, id))]

/** Opening `id`: unchanged if it already shows, else the oldest goes and it comes in far right. */
export const addRecent = (recent, id, tabs) =>
  stripOf(tabs, recent).some((t) => t.id === id) ? recent : [...recent.slice(1), id]

/** Saved text back to the list; anything broken or stale starts again from `seed`. */
export function readRecent(text, tabs, seed) {
  try {
    const recent = JSON.parse(text)
    const known = recent.every((id) => tabs.some((t) => t.id === id && !fixed(t)))
    if (known && recent.length === seed.length && new Set(recent.map((id) => withPartner(tabs, id)[0].id)).size === recent.length) return recent
  } catch {
    /* nothing saved yet */
  }
  return seed
}

/** The strip for `active`, remembered between visits. Every way into a tab passes here. */
export function useStrip(tabs, seed, active) {
  const [saved, save] = useRemembered('recent-tabs')
  const recent = useMemo(() => readRecent(saved, tabs, seed), [saved, tabs, seed])
  useEffect(() => {
    const next = addRecent(recent, active, tabs)
    if (next !== recent) save(JSON.stringify(next))
  }, [recent, active, tabs, save])
  return useMemo(() => stripOf(tabs, recent), [tabs, recent])
}
