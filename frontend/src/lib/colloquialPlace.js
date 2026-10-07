/**
 * Where the Colloquial tab is: "fusha", "fusha/unit-02", "fusha/unit-02/lesson-03",
 * or "fusha/unit-02/lesson-03/words" for that topic's words on their own.
 * Same shape as lib/hadithPlace, so a reload, a pasted link and the back arrow
 * all land on the same dialect, unit and topic.
 *
 * Pure: checked against the catalogue the panel already has. A unit or topic the
 * dialect has not written is no place, so a stale link opens the top, not a blank.
 * `at` is the topic's position in the unit, which is what the panel holds; `words`
 * is set only where the topic has a word list.
 */
export function parsePlace(q, dialects) {
  if (!q) return null
  const [dialectKey, unitKey, lessonKey, view, ...rest] = q.split('/')
  const dialect = dialects.find((d) => d.key === dialectKey)
  if (rest.length || !dialect) return null
  if (unitKey === undefined) return { dialect: dialectKey, unit: null, at: null }
  const unit = dialect.units.find((u) => u.written && u.unit === unitKey)
  if (!unit) return null
  if (lessonKey === undefined) return { dialect: dialectKey, unit: unitKey, at: null }
  const at = unit.lessons.findIndex((l) => l.written && l.lesson === lessonKey)
  if (at < 0 || (view !== undefined && (view !== 'words' || !unit.lessons[at].words))) return null
  return { dialect: dialectKey, unit: unitKey, at, words: view === 'words' }
}

export const placeOf = (dialect, unit, lesson, words = false) => [dialect, unit, lesson, words && 'words'].filter(Boolean).join('/')
