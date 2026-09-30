/**
 * The spots at the end of the tab strip. Fixed tabs (row 1, 2) always show;
 * any other tab opened takes the spot held longest, in place, so the strip
 * never grows. Replacing the oldest in place is taking the spots in turn,
 * hence one `next` pointer rather than a timestamp per spot.
 *
 * Pure: App keeps the result with useRemembered, so it survives a reload.
 */

const fixed = (tab) => tab.row < 3

// A half tab (Nahw, Sarf) fills one spot together with its partner.
function withPartner(tabs, id) {
  const tab = tabs.find((t) => t.id === id)
  return tab.half ? tabs.filter((t) => t.half && t.group === tab.group) : [tab]
}

/** Fixed tabs in list order, then the spots in place. Strip order = number keys. */
export const stripOf = (tabs, spots) => [...tabs.filter(fixed), ...spots.ids.flatMap((id) => withPartner(tabs, id))]

/** Saved text back to spots; anything broken or stale starts again from `seed`, far right replaced first. */
export function read(text, tabs, seed) {
  try {
    const { ids, next } = JSON.parse(text)
    const known = ids.every((id) => tabs.some((t) => t.id === id && !fixed(t)))
    const distinct = known && new Set(ids.map((id) => withPartner(tabs, id)[0].id)).size === ids.length
    if (ids.length === seed.length && distinct && Number.isInteger(next) && next >= 0 && next < ids.length) return { ids, next }
  } catch {
    /* nothing saved yet */
  }
  return { ids: seed, next: seed.length - 1 }
}

/** Opening `id`: unchanged if it already shows, else it takes the oldest spot. */
export function place(spots, id, tabs) {
  if (stripOf(tabs, spots).some((t) => t.id === id)) return spots
  return { ids: spots.ids.map((old, i) => (i === spots.next ? id : old)), next: (spots.next + 1) % spots.ids.length }
}
