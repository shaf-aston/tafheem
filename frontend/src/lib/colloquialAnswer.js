/**
 * Is this the right answer to a colloquial exercise?
 *
 * Marked here in the browser, not on the server: the accepted answers and the
 * options are in the unit the browser already holds, so a request per answer
 * would buy nothing but a wait. A graded assessment would be a different job and
 * would earn its own endpoint.
 *
 * Arabic is compared through recitedForm from lib/arabicText, the app's one
 * owner of this: a learner who writes a vowel mark differently, or the alif
 * without its hamza, has not made a mistake. It also drops the spaces, so a
 * missing space between two words is not a mistake either.
 *
 * A transliteration ("keefak?") has no Arabic letters, so recitedForm empties
 * it. Those are compared as plain lowercase letters and digits, which is what
 * the transliteration is written in.
 */
import { recitedForm } from './arabicText'

const latin = (text) => (text ?? '').toLowerCase().replace(/[^a-z0-9]/g, '')

/** Every form one written answer may be matched by. Empty forms are dropped so a
 *  blank reply matches nothing. */
const formsOf = (text) => [recitedForm(text), latin(text)].filter(Boolean)

/**
 * True when what the learner wrote is one of the exercise's accepted answers.
 * `accepted` already contains the answer itself, checked on the server.
 */
export const isRight = (written, accepted = []) => {
  const mine = formsOf(written)
  if (!mine.length) return false
  return accepted.some((one) => formsOf(one).some((form) => mine.includes(form)))
}

/**
 * The pieces a reorder exercise offers. `words` where the content names them,
 * otherwise the words of the answer itself, so a sentence is not written twice.
 * Punctuation is kept on the tile it belongs to: taking it off would ask the
 * learner to arrange words that are not the ones they will read.
 */
export const bankOf = (exercise) =>
  exercise.words?.length ? exercise.words : (exercise.answer ?? '').split(/\s+/).filter(Boolean)

/**
 * Right or wrong for any exercise type, so no component decides that itself.
 * A picked option must match exactly (it cannot be mistyped); a typed or arranged
 * answer goes through isRight. A reorder value is a list of words, joined here.
 */
export const judge = (exercise, value) => {
  if (exercise.type === 'choose') return value === exercise.answer
  const written = Array.isArray(value) ? value.join(' ') : value
  return isRight(written, exercise.accepted)
}

/** Whether there is anything to check yet: an empty box or an empty sentence is not an answer. */
export const hasAnswer = (value) => (Array.isArray(value) ? value.length > 0 : Boolean(value?.trim?.() ?? value))
