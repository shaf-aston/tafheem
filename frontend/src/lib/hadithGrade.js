/**
 * What a hadith's grading and a book's picture are, read from hadith.json.
 * Pure: the words live in config, this only applies them.
 */
import HADITH from '../hadith.json'

const { lead: LEAD, families: FAMILIES } = HADITH.grades

/** Which family a verdict falls in ('sound' | 'good' | 'weak'), or null for a wording none names. */
export function familyOf(grade) {
  const said = grade.toLowerCase()
  return FAMILIES.find((f) => f.words.some((w) => said.includes(w))) ?? null
}

/**
 * The verdict a card shows first: the leading scholar who graded it, else
 * the first who did. A Sahih collection grades every hadith itself, so a
 * hadith from one reads as sahih by that collection rather than by nobody.
 */
export function leadGrade(grades = [], sahihCollection = null) {
  if (!grades.length) return sahihCollection ? { by: sahihCollection, grade: 'Sahih' } : null
  return LEAD.map((name) => grades.find((g) => g.by === name)).find(Boolean) ?? grades[0]
}

/** The picture a book wears, by the first topic whose word its English name holds; null when none does. */
export function topicOf(bookName) {
  const name = bookName.toLowerCase()
  return HADITH.topics.find((t) => t.words.some((w) => name.includes(w)))?.id ?? null
}
