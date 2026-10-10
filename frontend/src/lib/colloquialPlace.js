/**
 * Where the Colloquial tab is: "fusha", "fusha/unit-02", "fusha/unit-02/lesson-03",
 * or "fusha/unit-02/lesson-03/words" for that topic's words on their own.
 * Same shape as lib/hadithPlace, so a reload, a pasted link and the back arrow
 * all land on the same dialect, unit and topic.
 *
 * Pure: checked against the catalogue the panel already has. A unit or topic the
 * dialect has not written is no place, so a stale link opens the top, not a blank.
 * `at` is the topic's position in the unit, which is what the panel holds; `words`
 * is set only where the topic has a word list. A place that is null is the top.
 */

/** The number in a unit id: unit-07 is 7. */
export const unitNumber = (id) => Number(id.replace(/\D/g, '')) || 0

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

/** The one writer: a place as its string, or null for the top. The reverse of parsePlace. */
export function placeOf(place, dialects) {
  if (!place) return null
  const { lessons } = dialects.find((d) => d.key === place.dialect).units.find((u) => u.unit === place.unit) ?? {}
  const lesson = typeof place.at === 'number' ? lessons[place.at].lesson : null
  return [place.dialect, place.unit, lesson, place.words && 'words'].filter(Boolean).join('/')
}

/** The same unit and topic in dialect `key`, as far as that dialect has written them. */
export function switchPlace(place, key, dialects) {
  const unit = dialects.find((d) => d.key === key).units.find((u) => u.written && u.unit === place.unit)
  const topic = unit && typeof place.at === 'number' && unit.lessons[place.at].written ? unit.lessons[place.at] : null
  return {
    dialect: key,
    unit: unit ? place.unit : null,
    at: topic ? place.at : null,
    words: Boolean(topic && place.words && topic.words > 0),
  }
}

/** The steps from the top down to `place`, each with where clicking it goes; the last is where you are. */
export function trailOf(place, dialects) {
  const steps = [{ label: 'Dialects', place: null }]
  if (!place) return steps
  const dialect = dialects.find((d) => d.key === place.dialect)
  steps.push({ label: dialect.label, place: { dialect: dialect.key, unit: null, at: null } })
  const unit = dialect.units.find((u) => u.written && u.unit === place.unit)
  if (!unit) return steps
  steps.push({ label: `Unit ${unitNumber(unit.unit)}`, place: { dialect: dialect.key, unit: unit.unit, at: null } })
  if (typeof place.at !== 'number') return steps
  steps.push({ label: unit.lessons[place.at].title, place: { dialect: dialect.key, unit: unit.unit, at: place.at, words: false } })
  if (place.words) steps.push({ label: 'Words', place })
  return steps
}

/** A place in words, for the way back: its topic's title, or its unit's, or the dialect. */
export function nameOfPlace(q, dialects) {
  const place = parsePlace(q, dialects)
  if (!place) return q
  const dialect = dialects.find((d) => d.key === place.dialect)
  const unit = dialect.units.find((u) => u.unit === place.unit)
  if (!unit) return dialect.label
  if (place.at === null) return unit.title
  const { title } = unit.lessons[place.at]
  return place.words ? `${title}: words` : title
}
