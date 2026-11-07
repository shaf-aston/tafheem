/**
 * This week on the learner's own days, Monday first, read from what the record says about days: the overview's
 * streak (days in a row, today counting once answered in) and each module's last answer. The store keeps no list
 * of days, so a day is only drawn as studied or not when the record proves it: a day of the streak or of a last
 * answer was studied; the day the streak broke, and every day after the last answer of all, was not. Any other
 * past day is left unknown rather than drawn as missed.
 */

const DAYS = 7

/** The local calendar day of `date`, as a key ("2026-11-07"): the learner's day, not UTC's. */
export const dayKey = (date) =>
  [date.getFullYear(), date.getMonth() + 1, date.getDate()].map((n) => String(n).padStart(2, '0')).join('-')

/** `date`'s local midnight moved `days` on; built from the calendar, so a clock change never skips a day. */
const shift = (date, days) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)

/**
 * Seven `{ date, state, today }`, Monday to Sunday of the week holding `now`. `state` is "studied", "rest" (the
 * record shows no answer), "unknown" (it does not say) or "ahead" (still to come, today included until answered in).
 * `overview` is fetchOverview's `{ streak, modules: [{ lastAt }] }`.
 */
export function weekOf(overview, now = new Date()) {
  const today = shift(now, 0)
  const last = overview.modules.map((row) => new Date(row.lastAt))
  const studied = new Set(last.map(dayKey))
  const answeredToday = studied.has(dayKey(today))
  // As the server counts it: the streak runs back from today once answered in, else from yesterday.
  const end = answeredToday ? today : shift(today, -1)
  for (let i = 0; i < overview.streak; i++) studied.add(dayKey(shift(end, -i)))
  const broke = dayKey(shift(end, -overview.streak))
  const latest = last.length ? dayKey(new Date(Math.max(...last))) : ''

  const monday = shift(today, -((today.getDay() + 6) % 7))
  return Array.from({ length: DAYS }, (_, i) => {
    const date = shift(monday, i)
    const key = dayKey(date)
    const isToday = key === dayKey(today)
    const state = studied.has(key) ? 'studied'
      : isToday || date > today ? 'ahead'
        : key === broke || key > latest ? 'rest' : 'unknown'
    return { date, state, today: isToday }
  })
}
