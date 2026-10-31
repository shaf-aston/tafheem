/**
 * Is this the right answer to a colloquial exercise?
 *
 * Marked here in the browser, not on the server: the accepted answers and the
 * options are in the unit the browser already holds, so a request per answer
 * would buy nothing but a wait. A graded assessment would be a different job and
 * would earn its own endpoint.
 *
 * Arabic is compared through recitedForm from lib/text/arabicText, the app's one
 * owner of this: a learner who writes a vowel mark differently, or the alif
 * without its hamza, has not made a mistake. It also drops the spaces, so a
 * missing space between two words is not a mistake either.
 *
 * A transliteration ("keefak?") has no Arabic letters, so recitedForm empties
 * it. Those are compared as plain lowercase letters and digits, which is what
 * the transliteration is written in.
 */
import { recitedForm } from '../text/arabicText'

// A transliteration as it sounds, not as it was spelt: Arabic-chat digits for
// letters English lacks (3 ayn, 2 hamza, 7 ha, 5 kha), e for i, o for u, ei for ay,
// a doubled letter as one. "wa 3aleikum es-salaam" and "wa alaykum is salam" meet.
const SOUNDS = [[/[32']/g, ''], [/7/g, 'h'], [/5|x/g, 'kh'], [/q/g, ''], [/ei|ai/g, 'ay'], [/e/g, 'i'], [/o/g, 'u'], [/(.)\1+/g, '$1']]
const latin = (text) => SOUNDS.reduce((t, [from, to]) => t.replace(from, to),
  (text ?? '').toLowerCase().replace(/[^a-z0-9']/g, ''))

const VOWEL = /[aiu]/
// Letters apart, where one vowel for another costs two: a vowel is often the whole
// difference between saying it to a man and to a woman (ismak, ismik).
function apart(a, b) {
  let row = Array.from({ length: b.length + 1 }, (_, j) => j)
  for (let i = 1; i <= a.length; i++) {
    const next = [i]
    for (let j = 1; j <= b.length; j++) {
      const swap = a[i - 1] === b[j - 1] ? 0 : VOWEL.test(a[i - 1]) && VOWEL.test(b[j - 1]) ? 2 : 1
      next.push(Math.min(row[j] + 1, next[j - 1] + 1, row[j - 1] + swap))
    }
    row = next
  }
  return row[b.length]
}
// A sentence long enough to carry one slip of spelling (an article written el- or
// es-, a letter left out); a short word must be spelt as it sounds.
const SLIP_FROM = 10

const near = (mine, theirs) => mine === theirs || (Math.min(mine.length, theirs.length) >= SLIP_FROM && apart(mine, theirs) <= 1)

/**
 * True when what the learner wrote is one of the exercise's accepted answers.
 * `accepted` already contains the answer itself, checked on the server. Arabic
 * is matched as recited; a transliteration as it sounds, one slip allowed in a
 * sentence.
 */
export const isRight = (written, accepted = []) => {
  const arabic = recitedForm(written)
  if (arabic) return accepted.some((one) => recitedForm(one) === arabic)
  const sounds = latin(written)
  if (!sounds) return false
  return accepted.some((one) => !recitedForm(one) && near(sounds, latin(one)))
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
 * The three ways an answer is given. Each says what the learner starts with
 * (`blank`) and how a value is marked (`judge`), so no component decides that
 * itself and nothing here asks which type an exercise is.
 */

/** Typed: goes through isRight. */
export const TYPED = { blank: '', judge: (exercise, value) => isRight(value, exercise.accepted) }

/** Picked: must match exactly, because a picked option cannot be mistyped. And
 *  `instant`: the pick is the answer, marked as it is made, as on the Quiz board. */
export const PICKED = { blank: '', instant: true, judge: (exercise, value) => value === exercise.answer }

/** Arranged: a list of words, joined here and then goes through isRight. */
export const ARRANGED = { blank: [], judge: (exercise, value) => isRight(value.join(' '), exercise.accepted) }

/** Whether there is anything to check yet: an empty box or an empty sentence is not an answer. */
export const hasAnswer = (value) => (Array.isArray(value) ? value.length > 0 : Boolean(value?.trim?.() ?? value))
