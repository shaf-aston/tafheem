/**
 * Whether a Tamreen tag answers to what was typed, typo tolerant with no AI.
 *
 * Same fold as exampleSearch: vowel marks off, alef variants folded, lower
 * case, letters compared as said rather than as written (see arabicText's
 * bareForm). Substring is tried first, on the tag's Arabic, English, key and
 * meaning; a search box that finds every exact match with no scoring is
 * simpler and does not need this file's second half.
 *
 * The second half is for a typo: each typed word is compared against every
 * word-prefix of the candidate text by edit distance, allowed distance 1 for
 * a short word and 2 for a longer one (tamreen.json), because one stray key
 * on a five-letter word is a plausible slip and the same slip on "of" would
 * match half the dictionary. A result found only this way is a "close match",
 * never presented as exact.
 *
 * Pure: strings in, a match verdict out.
 */
import { foldForSearch as fold } from './arabicText'
import { editDistance } from './editDistance'
import settings from '../tamreen.json'

// fold already turns punctuation into spaces: "(state)" is the word state.
const wordsOf = (text) => fold(text).split(/\s+/).filter(Boolean)

const allowedDistance = (word) =>
  word.length >= settings['typo-distance-long-min-length']
    ? settings['typo-distance-long']
    : settings['typo-distance']

/** True when `word` is within its allowed distance of some prefix of `candidate`. */
function fuzzyWordMatch(word, candidate) {
  const limit = allowedDistance(word)
  if (candidate.length <= word.length) return editDistance(word, candidate, limit) <= limit
  return editDistance(word, candidate.slice(0, word.length + limit), limit) <= limit
}

const FIELDS = (tag) => [tag.ar, tag.en, tag.key, tag.meaning]

/**
 * Whether every typed word is found in the tag, exactly (substring) or as a
 * typo of some word in the fields. Empty text matches everything, since an
 * empty box is not a filter.
 */
export function tagMatches(tag, typed) {
  return matchTag(tag, typed).hit
}

/**
 * Same question, with the answer split into exact vs close, so a search box
 * can label a fuzzy hit as a close match rather than showing it as if it were
 * typed correctly.
 */
export function matchTag(tag, typed) {
  const needle = fold(typed).trim()
  if (!needle) return { hit: true, exact: true }

  const fields = FIELDS(tag).filter(Boolean)
  if (fields.some((text) => fold(text).includes(needle))) return { hit: true, exact: true }

  const typedWords = needle.split(/\s+/).filter(Boolean)
  const candidateWords = fields.flatMap(wordsOf)
  const fuzzy = typedWords.every((word) => candidateWords.some((candidate) => fuzzyWordMatch(word, candidate)))
  return { hit: fuzzy, exact: false }
}
