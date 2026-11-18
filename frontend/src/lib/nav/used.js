/**
 * Which tabs the strip shows, from what the reader actually opens.
 *
 * The strip used to be eight tabs fixed in code (tabs.js FIXED and WIDE): a
 * reader who lives in Colloquial and Hadith had to go through All sections
 * every time, past five tabs they never open. Now the last few tabs chosen are
 * kept as plain text ("quran,dict,dict,colloq"), and the strip is Home, then
 * the tabs chosen most among them. The list is short on purpose: what was used
 * a month ago drops off on its own, so the strip follows a change of habit.
 *
 * Read once per visit (useState in useTabNavigation), never again while the app
 * is open: a tab must not change places under the pointer, or move its number
 * key, because it was just opened. A new order is the next visit's.
 *
 * Until enough choices are kept the strip is the default one, so a first visit
 * looks the way it always did.
 */
import config from '../../config/session.json'
import { readRaw, writeRaw } from '../store/stored'

const KEY = 'tab-uses'
const KEPT = config['tab-uses-kept']
const ENOUGH = config['tab-uses-to-order']

/** Saved text back to the choices, oldest first: unknown tabs dropped, at most KEPT. */
export function readUses(text, tabs) {
  const known = new Set(tabs.map((tab) => tab.id))
  return String(text ?? '').split(',').filter((id) => known.has(id)).slice(-KEPT)
}

/** The choices with `id` chosen once more, the oldest dropped past KEPT. */
export const addUse = (uses, id) => [...uses, id].slice(-KEPT)

/**
 * The strip's tabs in order: `home` first, then the most chosen of `tabs`, as
 * many places as `places` has. Ties, and tabs never chosen, keep `places`'s own
 * order, then the registry's, so a little use changes only a little.
 * Fewer than ENOUGH choices: `places` as it is.
 */
export function orderByUse(tabs, places, uses, home) {
  if (uses.length < ENOUGH) return places
  const count = new Map()
  for (const id of uses) count.set(id, (count.get(id) ?? 0) + 1)
  const rank = (id) => {
    const at = places.indexOf(id)
    return at === -1 ? places.length + tabs.findIndex((tab) => tab.id === id) : at
  }
  const rest = tabs.map((tab) => tab.id).filter((id) => id !== home)
  rest.sort((a, b) => (count.get(b) ?? 0) - (count.get(a) ?? 0) || rank(a) - rank(b))
  return [home, ...rest.slice(0, places.length - 1)]
}

/** The choices kept on this device. */
export const loadUses = (tabs) => readUses(readRaw(KEY), tabs)

/** Keep one more choice of `id`. */
export function noteUse(id, tabs) {
  if (!tabs.some((tab) => tab.id === id)) return
  writeRaw(KEY, addUse(loadUses(tabs), id).join(','))
}
