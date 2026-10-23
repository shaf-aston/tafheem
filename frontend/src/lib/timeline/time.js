/**
 * The time bar: where each event sits along it, which event a point on it is
 * nearest, the year marks under it, and the route walked up to an event.
 *
 * Pure: the bar and the map only draw this.
 */
import settings from '../../timelines.json'

const { scrub: SCRUB } = settings

/** How a section can be spread: true years only where its `at` is a year. */
export const scaleModes = (section) => (section.kind === 'dated' ? ['years', 'even'] : ['even'])

/**
 * Each event's place along the bar, 0 to 1. `years` keeps the real gaps (forty
 * quiet years, then twenty-three crowded ones); `even` gives every event the
 * same room. A section of one event, or one whose events share a year, is even.
 */
export function positions(section, mode) {
  const ats = section.events.map((e) => e.at)
  const n = ats.length
  const lo = ats[0]
  const span = ats.at(-1) - lo
  if (mode !== 'years' || !(span > 0)) return ats.map((_, i) => (n > 1 ? i / (n - 1) : 0))
  return ats.map((at) => (at - lo) / span)
}

/** The event nearest a point along the bar; the earlier one on a tie. */
export function nearest(pos, f) {
  let best = 0
  for (let i = 1; i < pos.length; i += 1) if (Math.abs(pos[i] - f) < Math.abs(pos[best] - f)) best = i
  return best
}

/**
 * Round years to mark under a true-years bar, each with its place along it:
 * the step is the smallest of the config's steps that keeps the count at or
 * under max-ticks.
 */
export function yearTicks(section) {
  const lo = section.events[0].at
  const hi = section.events.at(-1).at
  const span = hi - lo
  if (!(span > 0)) return []
  const step = SCRUB['tick-steps'].find((s) => span / s <= SCRUB['max-ticks']) ?? SCRUB['tick-steps'].at(-1)
  const ticks = []
  for (let year = Math.ceil(lo / step) * step; year <= hi; year += step) ticks.push({ year, at: (year - lo) / span })
  return ticks
}

/**
 * The places visited, in order, up to and including event `upTo`: one stop per
 * event with a place, a repeat of the stop before it left out (two events in
 * Madinah in a row are no journey).
 */
export function routeTo(section, upTo) {
  const stops = []
  section.events.slice(0, upTo + 1).forEach((e) => {
    if (e.place && stops.at(-1) !== e.place) stops.push(e.place)
  })
  return stops
}
