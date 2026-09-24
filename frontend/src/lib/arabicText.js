/**
 * Shared Arabic text helpers, the frontend's single owner of diacritics logic.
 * Never redefine these locally.
 *
 * Not a mirror of backend/services/arabic_text.py, though the diacritic ranges
 * are the same three. The backend also folds ٱ and ى→ي because it is lining up
 * two written sources; `bareForm` below deliberately does not, and says why.
 * Read them as two functions answering two questions, not as one that drifted.
 *
 * The ranges are written as explicit \u escapes so this can NEVER match an
 * Arabic letter: U+0610-U+061A (extended signs), U+064B-U+065F (harakat),
 * U+0670 (superscript alef). Same three ranges the backend strips.
 */

const DIACRITIC_CLASS = 'ؐ-ًؚ-ٰٟ'
const DIACRITICS = new RegExp(`[${DIACRITIC_CLASS}]`)
const DIACRITICS_ALL = new RegExp(`[${DIACRITIC_CLASS}]`, 'g')

// The hamza a writer puts on an alif is not reliably the same from one list to
// the next, so the three written forms fold back to the bare letter.
const ALIF_FORMS = /[أإآ]/g

/** True when the text carries at least one vowel mark (harakah). */
export const hasDiacritics = (text) => DIACRITICS.test(text ?? '')

/** True when the text contains an Arabic letter. Single source: SearchBox and
 * commandRoutes each had their own copy of this range, drifting apart. */
export const isArabic = (text) => /[؀-ۿ]/.test(text ?? '')

/**
 * Whether a text is written mainly in Arabic letters. Lane's entries sit where
 * a book's Arabic goes but are English with Arabic words in them, and set
 * right-to-left in the Arabic face they read backwards. Diacritics are not
 * counted, so a fully vowelled word does not outweigh a sentence.
 */
export const mostlyArabic = (text) =>
  (text?.match(/[ء-ي]/g)?.length ?? 0) > (text?.match(/[A-Za-z]/g)?.length ?? 0)

/**
 * One spelling of a word, so the same word written two ways still matches.
 *
 * Deliberately only these two steps. Folding ى into ي, or ة into ه, was measured
 * against the real word lists and matched not one extra word, it would only add
 * ways for two different words to collide.
 */
export const bareForm = (text) =>
  (text ?? '').replace(DIACRITICS_ALL, '').replace(ALIF_FORMS, 'ا')

// Three more things the Qur'anic printing writes that no keyboard offers: the
// wasla alif ٱ, the dagger-alif ى standing for a long a, and the tatweel ـ used
// to stretch a line. Nobody filling in a gap types any of them.
const UNTYPEABLE = /[ٱ]/g          // ٱ → ا
const ALIF_MAQSURA = /ى/g          // ى → ي
const TATWEEL = /ـ/g
// Whatever is not an Arabic letter: the ۞ and ۩ marks, ayah numbers, brackets,
// and any punctuation a reader might type around a word.
const NOT_A_LETTER = /[^ء-ي]/g

/**
 * A word as it is said, for comparing something typed against something
 * printed. Everything bareForm folds, plus the three marks above and anything
 * that is not a letter.
 *
 * Deliberately harsher than bareForm and deliberately not a replacement for it.
 * bareForm lines up two written sources, where ٱ and ى carry real information
 * about which word it is; this one is used where a person typed the answer on a
 * keyboard that has no key for either. Letters still count: ة and ه are not
 * folded together, because they are different words and accepting one for the
 * other would teach the wrong spelling.
 */
export const recitedForm = (text) =>
  bareForm(settled(text))
    .replace(UNTYPEABLE, 'ا')
    .replace(ALIF_MAQSURA, 'ي')
    .replace(TATWEEL, '')
    .replace(NOT_A_LETTER, '')

// The standing fatha ٰ (U+0670). It is a harakah, it marks a long a, but the
// Qur'anic printing uses it where later spelling put a whole alif letter, so
// the two spellings differ by a letter and not only by a mark.
const STANDING_FATHA = /ٰ/g
// Sitting on a letter that is already that long, it adds nothing: عَلَىٰ is على.
const ALREADY_LONG = /([اى])ٰ/g

const settled = (text) => (text ?? '').replace(ALREADY_LONG, '$1')

/**
 * Every spelling of one word that a reader could reasonably type.
 *
 * One word, two written forms, and which one a word takes is a fact about that
 * word rather than a rule: ٱلصَّٰلِحَٰتِ is written ٱلصالحات with the alif, while
 * ذَٰلِكَ is written ذلك without it. Nothing in the text says which, so guessing
 * would mark a right answer wrong, as it did, and a word list would only move
 * the guess into a file. Both are therefore accepted.
 */
export const recitedForms = (text) => {
  const one = settled(text)
  return new Set([recitedForm(one), recitedForm(one.replace(STANDING_FATHA, 'ا'))])
}

/**
 * True when two spellings are the same word said aloud. Empty matches nothing,
 * so an untouched gap is never right.
 */
export const sameSpokenWord = (typed, printed) => {
  const theirs = recitedForms(printed)
  return [...recitedForms(typed)].some((form) => form !== '' && theirs.has(form))
}
