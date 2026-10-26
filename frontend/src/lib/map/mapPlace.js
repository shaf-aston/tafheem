/**
 * The Map's screens as addresses: /map (the nine sciences), /map/07 (a chart), /map/07/2/0 (a box inside
 * it, by child number from the root), /map/manhaj/creed (a family of methodologies), /map/manhaj/creed/ibadi
 * (a group's page), /map/manhaj/creed/ibadi/ashari (that page compared with another group).
 * Pure. `placeOf` reads the tab's value (lib/nav/tabUrl.js writes it), `valueOf` writes one; MapPanel is the caller.
 * Anything unknown falls back to the nearest place that exists.
 */
import { nodeAt } from '../shell/pbsTree'

export const MANHAJ = 'manhaj'

/** A family's place from the pieces after "manhaj"; an unknown group or comparison is dropped. */
function manhajPlace(families, [familyId, groupId, otherId]) {
  const family = families.find((one) => one.id === familyId) ?? families[0]
  const has = (id) => family.groups.some((one) => one.id === id)
  if (family.id !== familyId || !has(groupId)) return { at: MANHAJ, family: family.id }
  const other = otherId !== groupId && has(otherId) ? otherId : null
  return { at: MANHAJ, family: family.id, group: groupId, ...(other && { other }) }
}

/** `{ at: 'index' }`, `{ at: 'chart', id, path }` or `{ at: 'manhaj', family, group?, other? }`. */
export function placeOf(value, charts, families) {
  const [first, ...rest] = (value ?? '').split('/').filter(Boolean)
  if (first === MANHAJ) return manhajPlace(families, rest)
  if (!charts.some((chart) => chart.id === first)) return { at: 'index' }
  const path = rest.map(Number)
  const whole = path.findIndex((n) => !Number.isInteger(n) || n < 0)
  return { at: 'chart', id: first, path: whole < 0 ? path : path.slice(0, whole) }
}

/** The tab value for a screen: null for the index. */
export function valueOf(place) {
  if (place.at === 'chart') return [place.id, ...place.path].join('/')
  if (place.at === MANHAJ) return [MANHAJ, place.family, place.group, place.other].filter(Boolean).join('/')
  return null
}

/** The longest start of `path` that names a box in `tree`: an address from an older chart still opens near its place. */
export function reachable(tree, path) {
  let n = path.length
  while (n > 0 && !nodeAt(tree, path.slice(0, n))) n -= 1
  return n === path.length ? path : path.slice(0, n)
}

/** One level up: a box's parent, a chart's index, a group's family, a family's index. */
export function upOf(place) {
  if (place.at === 'chart' && place.path.length) return { ...place, path: place.path.slice(0, -1) }
  if (place.at === MANHAJ && place.group) return { at: MANHAJ, family: place.family }
  return { at: 'index' }
}

/** Which screen a place is, apart from a comparison picked on it: a new screen opens at its top, a comparison does not move the page. */
export const screenOf = (place) => valueOf({ ...place, other: null }) ?? ''
