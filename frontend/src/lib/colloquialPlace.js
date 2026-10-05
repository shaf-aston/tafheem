/**
 * Where the Colloquial tab is: "fusha", "fusha/unit-02", or "fusha/unit-02/lesson-03".
 * Same shape as lib/hadithPlace, so a reload, a pasted link and the back arrow
 * all land on the same dialect, unit and topic.
 *
 * Pure: checked against the catalogue the panel already has. A unit or topic the
 * dialect has not written is no place, so a stale link opens the top, not a blank.
 * `at` is the topic's position in the unit, which is what the panel holds.
 */
export function parsePlace(q, dialects) {
  if (!q) return null
  const [dialectKey, unitKey, lessonKey, ...rest] = q.split('/')
  const dialect = dialects.find((d) => d.key === dialectKey)
  if (rest.length || !dialect) return null
  if (unitKey === undefined) return { dialect: dialectKey, unit: null, at: null }
  const unit = dialect.units.find((u) => u.written && u.unit === unitKey)
  if (!unit) return null
  if (lessonKey === undefined) return { dialect: dialectKey, unit: unitKey, at: null }
  const at = unit.lessons.findIndex((l) => l.written && l.lesson === lessonKey)
  return at < 0 ? null : { dialect: dialectKey, unit: unitKey, at }
}

export const placeOf = (dialect, unit, lesson) => [dialect, unit, lesson].filter(Boolean).join('/')
