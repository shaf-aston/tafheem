/**
 * Whether a worked example is the one somebody is typing.
 *
 * Four things are looked in, and every one of them is on the card in front of
 * the reader: the sentence, its English, and the grammar topic the card is
 * labelled with, in Arabic and in English. The topic is why this exists. The
 * card said الْجُمْلَةُ الْفِعْلِيَّةُ in its corner and typing that found nothing,
 * because only the sentence and the translation were ever looked at.
 *
 * Both sides have their vowel marks taken off first. The books print their
 * sentences fully vowelled and nobody types those marks, so comparing the
 * letters as written meant a copy and paste was the only thing that could ever
 * match. That is what made the box unable to find its own example: it invited
 * كتاب and every كتاب in the books is written كِتَابٌ.
 *
 * Deliberately not fuzzy: the marks come off, capitals are flattened, nothing
 * else. A match is still the letters that were typed, in the order typed.
 *
 * Pure: strings in, true or false out.
 */
import { bareForm } from './arabicText'

/** One side of the comparison: no vowel marks, no capitals. */
const fold = (text) => bareForm(text).toLowerCase()

/**
 * True when this example answers to what was typed. Empty text matches every
 * example, since an empty box is not a filter.
 *
 * The topic is allowed to be missing, which happens when an example names a
 * topic the topic list does not. That loses the two topic names for that one
 * card rather than losing the card.
 */
export function exampleMatches(example, topic, typed) {
  const needle = fold(typed).trim()
  if (!needle) return true
  return [example.sentence, example.translation, topic?.ar, topic?.en].some(
    (text) => text && fold(text).includes(needle),
  )
}
