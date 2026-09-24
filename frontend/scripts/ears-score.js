/**
 * What a reader would have seen on the page for one ayah, as counts.
 *
 * A plain module, not part of ears.test.js, for the same reason ears-local.js
 * is one: `npm test` collects every scripts/*.test.js file, and a test for
 * this function has to import it from somewhere that isn't itself a
 * benchmark describe block.
 */
import { follow, isOfPage, wordsHeard } from '../src/lib/follow'

/**
 * A pause mark stands on its own between two words, with a space on each side:
 * ۖ in 2:127, ۚ in 3:104. Split on spaces and it looks like a word, and a word
 * nobody can ever say, so every ayah carrying one counted a missed word that
 * was never there. It cost about three points of every ear's score.
 */
const isWord = (token) => /[ء-ي]/.test(token)

export const score = (printed, said) => {
  const page = printed.split(/\s+/).filter(isWord)
  const heard = wordsHeard(said)
  const tally = { words: page.length, wrong: 0, check: 0, missed: 0, extra: 0, quiet: 0 }
  // A reading with nothing of the page in it never reaches the page at all;
  // the reciting session drops it, so counting its words as mistakes would be a lie -
  // but it is not free either, so every page word is counted missed, the same
  // as a reader would see a blank ayah. Otherwise a model that heard nothing
  // printed a perfect 0.0% row.
  if (!isOfPage(heard, page)) { tally.quiet = 1; tally.missed = page.length; return tally }
  const marks = follow(page, heard, { ended: true })
  for (const { state } of marks.words) {
    if (state === 'wrong') tally.wrong += 1
    if (state === 'check') tally.check += 1
    if (state === 'missed') tally.missed += 1
  }
  tally.extra = marks.extras.length
  return tally
}
