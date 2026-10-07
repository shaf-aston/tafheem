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

// Punctuation is a break between words, never part of one, except an apostrophe
// between two letters (don't, Mu'adh). The same rule as the backend's
// arabic_text.unpunctuated, which every server search reads its query by.
const PUNCTUATION = /(?:(?!(?<=\p{L})['’](?=\p{L}))\p{P})+/gu
// @ and / start a command (lib/commandRoutes) and are never trimmed off.
const TRAILING = /(?:\s|(?![@/])\p{P})+$/u

/** The text with every punctuation mark a space: "القيامة." is القيامة. */
export const unpunctuated = (text) => (text ?? '').replace(PUNCTUATION, ' ')

/** A typed line without what trails off its end: "2:255." and "2:255؟" are 2:255. */
export const untrailed = (text) => (text ?? '').trim().replace(TRAILING, '')

/** One side of a search comparison: no vowel marks, no capitals, no punctuation. Null is empty. */
export const foldForSearch = (text) => bareForm(unpunctuated(text)).toLowerCase()

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

// ة and ه sound the same at the end of a spoken word, and colloquial spelling
// is not standardised, so for speech the two are one letter.
const TA_MARBUTA = /ة/g

/**
 * A phrase as it is spoken, for checking a typed or transcribed answer in
 * Colloquial. Unlike recitedForm it keeps word breaks (answers are whole
 * phrases) and folds ة into ه (spoken, not spelled): anything that is not a
 * letter becomes one space.
 */
export const spokenForm = (text) =>
  bareForm(text)
    .replace(TATWEEL, '')
    .replace(ALIF_MAQSURA, 'ي')
    .replace(TA_MARBUTA, 'ه')
    .replace(NOT_A_LETTER, ' ')
    .replace(/ +/g, ' ')
    .trim()

// Letters joining nothing after them (ا د ذ ر ز و and the hamza and final forms).
const JOINS_NOTHING_ONWARD = 'ءاأإآٱدذرزوؤةى'
// Letters a small alef after needs no seat for: those joining nothing onward,
// ى that carries it itself (هُدَىٰهُمْ), and a tatweel already standing.
const NEEDS_NO_SEAT = new Set(`${JOINS_NOTHING_ONWARD}ـ`)
const isLetter = (c) => (c >= 'ء' && c <= 'ي') || c === 'ٱ'
const isMark = (c) => (c >= 'ً' && c <= 'ٟ') || c === 'ٰ' || (c >= 'ۖ' && c <= 'ۭ')

/**
 * A piece cut from the front of a written word, drawn joined on to what follows
 * as the script writes it: فَـ and لْـ take a joining stroke, وَ never joins on.
 */
export const joinsOn = (piece) => {
  const last = [...piece].reverse().find(isLetter)
  return Boolean(last) && !JOINS_NOTHING_ONWARD.includes(last)
}
export const joinedOn = (piece) => (joinsOn(piece) ? `${piece}ـ` : piece)

/**
 * The mushaf's spelling as a font draws it: a small alef between two joined
 * letters stands on a tatweel, أُو۟لَـٰٓئِكَ, as the Tanzil and King Fahd texts
 * write it. Without that seat its vowel, the small alef and a madda all stack
 * on the one letter. Text with no small alef is returned as it came.
 */
export const seatSmallAlef = (text) => {
  if (typeof text !== 'string' || !text.includes('ٰ')) return text
  const chars = [...text]
  const near = (i, step) => {
    while (isMark(chars[i] ?? '')) i += step
    return chars[i] ?? ''
  }
  return chars.map((c, i) => {
    if (c !== 'ٰ') return c
    const before = near(i - 1, -1)
    const seated = isLetter(before) && !NEEDS_NO_SEAT.has(before) && isLetter(near(i + 1, 1))
    return seated ? `ـ${c}` : c
  }).join('')
}

/**
 * True when the text is in the mushaf's own spelling: it carries the alef wasla
 * or a mark from U+06D6 to U+06ED (small high letters, rounded sukun, waqf
 * signs), which typed or printed Arabic never does.
 */
export const isQuranic = (text) =>
  [...(text ?? '')].some((char) => {
    const code = char.codePointAt(0)
    return code === 0x0671 || (code >= 0x06d6 && code <= 0x06ed)
  })

/** The text inside a piece of React markup, however deeply nested. */
export const textOf = (node) => {
  if (node == null || typeof node === 'boolean') return ''
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(textOf).join('')
  return textOf(node.props?.children)
}
