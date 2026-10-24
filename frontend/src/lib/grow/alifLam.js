/**
 * The Basics world's first skill: ال means "the". Pure.
 *
 * Every wrong option is the item's own word written the way a beginner gets it wrong, so the
 * question is only ever "is ال there, and is it written right?", never "which word is it?":
 *   bare     كِتَاب       ال forgotten
 *   tanween  الْكِتَابٌ    ال with tanween, which never go together
 *   apart    ال كِتَاب    ال written as a word of its own, like "the"
 *   heard    اشَّمْس      spelt as said: before a sun letter the ل is silent, but it is still written
 *            (never for ل: الَّيْل is how the Qur'an's script writes it)
 * Words come from public/grow/basics.json (bare, vowelled, no ال); the path they sit on is lib/grow/basicsSkills.js.
 */
import { shuffled } from '../text/shuffle'
import { moduleOf } from './worlds'

export const MODULE = moduleOf('basics')

// The fourteen letters ال's ل blends into (ash-shams); the other fourteen keep it (al-qamar).
export const SUN_LETTERS = new Set([...'تثدذرزسشصضطظلن'])

const SHADDA = '\u0651'
const SUKUN = '\u0652'
const DAMMATAN = '\u064C'
const MARKS = /[\u064B-\u0652\u0670]/
// Tanween at the end, and the alif written after fathatan (كِتَابًا).
const TANWEEN = /[\u064B-\u064D]\u0627?$/u

const nfc = (text) => text.normalize('NFC')
const firstLetter = (bare) => [...bare].find((char) => !MARKS.test(char))
const afterFirst = (bare) => bare.slice(bare.indexOf(firstLetter(bare)) + 1)

/** The word with any tanween taken off. */
export const plain = (bare) => nfc(bare.trim().replace(TANWEEN, ''))

export const isSun = (bare) => SUN_LETTERS.has(firstLetter(plain(bare)))

/** "the" + word: a sun letter takes a shadda and the ل no sukun (الشَّمْس); a moon letter keeps the ل (الْقَمَر). */
export function definite(bare) {
  const word = plain(bare)
  return nfc(isSun(word) ? `ال${firstLetter(word)}${SHADDA}${afterFirst(word)}` : `ال${SUKUN}${word}`)
}

/** Each wrong form, or null where it does not apply to this word. */
export const FORMS = {
  bare: (bare) => plain(bare),
  tanween: (bare) => nfc(`${definite(bare)}${DAMMATAN}`),
  apart: (bare) => `ال ${plain(bare)}`,
  // Not for ل: الَّيْل is how the Qur'an's own script writes اللَّيْل (وَٱلَّيْلِ, 92:1), so it cannot be shown as a mistake.
  heard: (bare) => (isSun(bare) && firstLetter(plain(bare)) !== 'ل' ? nfc(`ا${firstLetter(plain(bare))}${SHADDA}${afterFirst(plain(bare))}`) : null),
}

/** The two wrong forms asked beside the right one: always the word without ال, then its sun-letter spelling, else one of the other two. */
export function wrongForms(bare, random) {
  const second = FORMS.heard(bare) ? 'heard' : random() < 0.5 ? 'tanween' : 'apart'
  return ['bare', second]
}

export const article = (word) => word.a ?? (/^[aeiou]/i.test(word.en) ? 'an' : 'a')

export const english = (word, isDefinite) => `${isDefinite ? 'the' : article(word)} ${word.en}`

export const keyOfBasic = (word) => word.id

const record = (word, direction) => ({ module: MODULE, item: word.id, context: { world: MODULE, direction, word: plain(word.ar) } })
const tagOf = (isNew) => (isNew ? 'New word' : 'Review')

function whyArabic(word) {
  const the = definite(word.ar)
  const said = `${the} = ${english(word, true)}.`
  return isSun(word.ar)
    ? `${said} The ل of ال is written, but not said: it joins the ${firstLetter(plain(word.ar))} after it.`
    : `${said} ال is joined to the front of the word, and a word with ال never ends in -un (ـٌ).`
}

// What each wrong form got wrong, said after the right answer when it is the one picked.
const MISTAKES = {
  bare: (word) => `${plain(word.ar)} has no ال: it is “${english(word, false)}”.`,
  tanween: () => 'ال and the -un ending (ـٌ) never go together.',
  apart: () => 'ال is joined to the front of the word, never written apart.',
  heard: (word) => `The ل is not said before ${firstLetter(plain(word.ar))}, but it is still written.`,
}

/** "the book" → pick the Arabic: the right form and two of the word's own wrong forms. */
export function toArabicCard(word, isNew, random) {
  const right = { id: 'right', text: definite(word.ar) }
  const types = wrongForms(word.ar, random)
  const wrong = types.map((type) => ({ id: type, text: FORMS[type](word.ar) }))
  const said = `${definite(word.ar)} = ${english(word, true)}.`
  return {
    kind: 'choose',
    id: `the:${word.id}`,
    tag: tagOf(isNew),
    ask: `Which one is “${english(word, true)}”?`,
    arabic: true,
    options: shuffled([right, ...wrong], random),
    answer: 'right',
    why: whyArabic(word),
    wrong: Object.fromEntries(types.map((type) => [type, `${said} ${MISTAKES[type](word)}`])),
    record: record(word, 'to-arabic'),
  }
}

/** The word with or without ال, at random → "the book" or "a book". */
export function toEnglishCard(word, isNew, random) {
  const isDefinite = random() < 0.5
  const shown = isDefinite ? definite(word.ar) : plain(word.ar)
  // Never two Arabic words with only a comma or space between them: in a left-to-right line they swap places.
  const why = isDefinite
    ? `ال at the start means “the”: ${shown} = ${english(word, true)}.`
    : `No ال at the start, so it is “${english(word, false)}”. Add ال and it is “${english(word, true)}”: ${definite(word.ar)}.`
  return {
    kind: 'choose',
    id: `means:${word.id}`,
    tag: tagOf(isNew),
    ask: 'What does it mean?',
    ar: shown,
    options: shuffled([{ id: 'the', text: english(word, true) }, { id: 'a', text: english(word, false) }], random),
    answer: isDefinite ? 'the' : 'a',
    why,
    record: record(word, 'to-english'),
  }
}

/** Said once, before a first lesson's first word. */
export const INTRO = {
  kind: 'teach',
  id: 'teach:al',
  tag: 'New',
  ar: 'ال',
  en: 'means “the”',
  // definite('كِتَاب'), written out so nothing is worked out as the file loads (alifLam.test.js checks they match).
  also: { ar: 'الْكِتَاب', en: 'the book' },
}

/** A new word: with ال, and without it. */
export const teachWord = (word) => ({
  kind: 'teach',
  id: `teach:${word.id}`,
  tag: 'New word',
  ar: definite(word.ar),
  en: english(word, true),
  also: { ar: plain(word.ar), en: english(word, false) },
})

/** A word asked both ways. The Basics path that weaves these with the other skills: lib/grow/basicsSkills.js. */
export const wordAsks = (word, isNew, random) => [toArabicCard(word, isNew, random), toEnglishCard(word, isNew, random)]
