/**
 * Whether a book is the one somebody is typing the name of.
 *
 * Two names are tried, the book's own and its English one, because half the
 * library is called مختصر القدوري and the reader is typing on an English
 * keyboard.
 *
 * The harder half is that there is no single English spelling of an Arabic
 * name. The same book is written Quduri, Qudoori, al-Kuduri; ق is a q to one
 * person and a k to another, and a long vowel is doubled by one writer and not
 * by the next. Matching the letters exactly would mean the reader has to guess
 * the one spelling this app happens to have chosen, which is the same dead end
 * as not being able to type Arabic. So both sides are folded to a rough shape
 * first, and the shape is what is compared.
 *
 * Deliberately not fuzzy: no edit distance, no scoring, no ranking. Every rule
 * here is a spelling choice that Arabic romanisation genuinely leaves open, so
 * a match is still a real match and a reader is never shown a book because it
 * was two typos away. Arabic text passes through untouched, so typing Arabic
 * behaves exactly as it always did.
 *
 * Pure: strings in, boolean out.
 */

// The article, which people leave off as often as they write it: nobody
// searching for al-Hidaya types the al. Hyphens have become spaces by the time
// this runs, so "al-Hidaya" and "al Hidaya" are one thing, and only a
// standalone al goes, never the al inside Alfiyya or Jalalayn.
const ARTICLE = /\b(?:al|el)\s+/g

const SEPARATORS = /[-_'’ʼ‘`.,()]+/g  // apostrophes and dashes are punctuation here, not sounds
// Any mark sitting on a letter: an accent from a fancier romanisation, or a
// haraka on Arabic, neither of which anyone types into a filter box.
const MARKS = /\p{M}/gu
const SPACES = /\s+/g

/** The rough shape of a name, with the spellings nobody agrees on flattened. */
function fold(text) {
  return text
    .normalize('NFD')
    .replace(MARKS, '')
    .toLowerCase()
    .replace(SEPARATORS, ' ')
    // Long vowels, written doubled by some and single by others. Done before
    // the doubles are collapsed below, or oo would flatten to o and never meet
    // the u that the same sound is usually written with.
    .replace(/oo/g, 'u')
    .replace(/ee/g, 'i')
    // ق, a q to one writer and a k to another. Quduri and Kuduri are one book.
    .replace(/q/g, 'k')
    // A doubled consonant is a shadda, and whether it survives romanisation is
    // a coin toss: Ajurrumiyya, Ajurumiya.
    .replace(/([a-z])\1+/g, '$1')
    .replace(SPACES, ' ')
    .replace(ARTICLE, '')
    .trim()
}

/**
 * True when this book answers to what was typed. Empty text matches every
 * book, since an empty filter is not a filter.
 */
export function nameMatches(book, typed) {
  const needle = fold(typed)
  if (!needle) return true
  return [book.name, book.english].some((name) => name && fold(name).includes(needle))
}
