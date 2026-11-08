/**
 * This week on the learner's own days, Monday first, from the overview's `days`: the local days answered in over
 * the last two weeks, as the server counts them in the learner's time zone (backend services/learner/attempts.py
 * overview). Two weeks, so a Sunday still sees its Monday.
 */

const DAYS = 7

/** The local calendar day of `date`, as a key ("2026-11-07"): the learner's day, not UTC's. */
export const dayKey = (date) =>
  [date.getFullYear(), date.getMonth() + 1, date.getDate()].map((n) => String(n).padStart(2, '0')).join('-')

/** `date`'s local midnight moved `days` on; built from the calendar, so a clock change never skips a day. */
const shift = (date, days) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)

/**
 * Seven `{ date, state, today }`, Monday to Sunday of the week holding `now`. `state` is "studied", "rest" (a day
 * gone by with no answer) or "ahead" (still to come, today included until answered in). `overview` is fetchOverview's.
 */
export function weekOf(overview, now = new Date()) {
  const today = shift(now, 0)
  const studied = new Set(overview.days ?? [])
  const monday = shift(today, -((today.getDay() + 6) % 7))
  return Array.from({ length: DAYS }, (_, i) => {
    const date = shift(monday, i)
    const key = dayKey(date)
    const state = studied.has(key) ? 'studied' : date < today ? 'rest' : 'ahead'
    return { date, state, today: key === dayKey(today) }
  })
}
