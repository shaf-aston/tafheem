/**
 * Turns the dictionary's academic spelling of a word's sound into one an
 * English reader can say without being taught a symbol set first.
 *
 * Wiktionary ships every entry romanised in the scholarly standard (DIN 31635),
 * where one symbol means exactly one Arabic letter, so a specialist can rebuild
 * the Arabic spelling from the romanisation alone. That is a real property, and
 * a useless one to a learner who has to stop and decode `ʔūrūbbā š-šarqiyya`.
 *
 * So the trade this module makes, on purpose: the letter pairs English already
 * knows (sh, th, kh, gh) instead of single marked symbols, and a doubled vowel
 * for a long one. What is lost is the five emphatic pairs, ص and س both become
 * s, ح and ه both h. That loss is affordable here and nowhere else: this text
 * is only ever printed beside the Arabic word itself, which is the real record
 * of which letter it was.
 *
 * The stored value is never altered. Conversion happens at display time, so the
 * academic form stays in the data and changing this scheme is a change to this
 * file only.
 *
 * Pure: string in, string out. No React, no config, no I/O.
 */

/**
 * Every non-English symbol the dump uses, and what to print instead.
 *
 * Complete, not a sample: these are the 28 characters that actually occur
 * across the 23,174 romanised entries in arabic_dictionary.json. Anything not
 * listed passes through untouched, so a new symbol appearing in a future dump
 * degrades to showing itself rather than vanishing.
 */
const LETTERS = {
  // Hamza and ayn. Both are throat sounds English has no letter for; an
  // apostrophe is the usual stand-in for both, which is why they merge here.
  'ʔ': "'", 'ʕ': "'", 'ʾ': "'", 'ʿ': "'", '‘': "'",

  // Long vowels. Doubling is what keeps this scheme honest for a grammar tool:
  // length is the whole difference between فَعَل and فَاعَل, so dropping the
  // macron rather than doubling would erase a grammatical fact, not a nicety.
  'ā': 'aa', 'ī': 'ee', 'ū': 'oo', 'ō': 'oo', 'ē': 'ee', 'Ā': 'Aa',
  'á': 'a', 'í': 'i',

  // Sounds English writes with two letters.
  'ṯ': 'th', 'ḏ': 'dh', 'ḵ': 'kh', 'ḡ': 'gh', 'š': 'sh', 'ž': 'zh', 'ğ': 'j',
  'Ḏ': 'Dh',

  // The emphatic letters, each printed as its plain English neighbour.
  'ḥ': 'h', 'ṣ': 's', 'ḍ': 'd', 'ṭ': 't', 'ẓ': 'z', 'Ḥ': 'H', 'Ṣ': 'S',
}

// An apostrophe opening a word. Dropped: nobody pronounces the catch before a
// first vowel as a separate thing, and "'arabiyya" reads as a typo where
// "arabiyya" reads as a word. Kept inside or at the end of a word, where it is
// a sound the reader can hear (sahraa', mas'ala).
//
// "Opening a word" is the whole condition, which is why a letter has to follow.
// One definition names the letter itself, ا (ʔ) and و (w) and ي (y), and a rule
// that only looked to the left would turn that into an empty pair of brackets.
const OPENING = /(^|[^A-Za-z'])'+(?=[A-Za-z])/g

// A sound written between slashes is IPA, a different alphabet that happens to
// share some of these symbols, and in the handful of entries that use it the
// symbol is what the sentence is about: "the glottal stop /ʔ/". Rewriting that
// to /'/ would make the sentence false. No spaces allowed inside, so an
// ordinary "genitive/possessive" pair of slashes is not mistaken for it.
const IPA = /(\/[^/\s]*\/)/g

/**
 * The same text with the academic spelling read out in English letters.
 *
 * Takes either a bare romanisation ("kitāb") or a sentence with romanisations
 * inside it ("verbal noun of كَاتَبَ (kātaba)"), because the dictionary prints
 * both and they need to agree on the same card. Empty in, empty out.
 */
export function plainPronunciation(scholarly) {
  if (!scholarly) return ''
  // NFC first: a marked letter can arrive either precomposed or as a letter
  // plus a combining mark, and only the precomposed form is in the table.
  return scholarly.normalize('NFC')
    .split(IPA)
    // split with a capturing group hands back text, delimiter, text, delimiter:
    // the odd places are the IPA that must survive untouched.
    .map((piece, at) => (at % 2 ? piece : swap(piece)))
    .join('')
}

function swap(text) {
  const swapped = [...text].map((character) => LETTERS[character] ?? character).join('')
  return swapped.replace(OPENING, '$1')
}
