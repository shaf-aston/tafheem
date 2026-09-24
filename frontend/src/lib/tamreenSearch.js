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
import { bareForm } from './arabicText'
import settings from '../tamreen.json'

const fold = (text) => bareForm(text ?? '').toLowerCase()
// Punctuation stripped only for the word list the fuzzy match walks: "(state)"
// is not a typo of "state" away from its own parentheses, it is the same word
// wearing punctuation that a typed query never carries.
const PUNCTUATION = /[^\p{L}\p{N}\s]/gu
const wordsOf = (text) => fold(text).replace(PUNCTUATION, ' ').split(/\s+/).filter(Boolean)

const allowedDistance = (word) =>
  word.length >= settings['typo-distance-long-min-length']
    ? settings['typo-distance-long']
    : settings['typo-distance']

/**
 * Levenshtein edit distance between two strings, capped: once every entry in
 * the row exceeds `max` the words cannot possibly match, so the loop stops
 * and reports "too far" rather than finishing the full table for nothing.
 */
function editDistance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i)
  for (let i = 1; i <= a.length; i++) {
    const row = [i]
    let rowMin = i
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      const value = Math.min(row[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
      row.push(value)
      rowMin = Math.min(rowMin, value)
    }
    if (rowMin > max) return max + 1
    prev = row
  }
  return prev[b.length]
}

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
