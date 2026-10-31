/**
 * A noun in a short phrase, for the Basics world. Pure. Each table is every form of one word as entries { key, ar, en },
 * like lib/grow/wordForms.js's, and is asked with its pickers:
 *   peopleTable(person)   مُسْلِم · مُسْلِمَة · مُسْلِمُونَ · مُسْلِمَات: a man, a woman, men, women
 *   joinedTable(word)     وَالْكِتَاب and the book · بِالْقَلَم with the pen · لِلْبَيْت for the house · كَالْقَمَر like the moon
 *   pointingTable(word)   هٰذَا كِتَاب this is a book · هٰذَا الْكِتَاب this book · تِلْكَ سَيَّارَة that is a car …
 *   pronounTable(person)  هُوَ مُسْلِم he is a Muslim · هِيَ مُسْلِمَة she is a Muslim · نَحْنُ مُسْلِمُونَ we are Muslims …
 *   ofTable(pair)         كِتَاب الْمُعَلِّم the teacher’s book · كِتَاب مُعَلِّم a teacher’s book · مُعَلِّم الْكِتَاب the book’s teacher
 *   dualTable(word)       كِتَابَانِ two books · الْكِتَابَانِ the two books · سَيَّارَتَانِ two cars
 * plus forms a beginner builds wrongly (en null): *وَ الْكِتَاب, *لِالْكِتَاب, *هٰذِهِ كِتَاب, *هِيَ مُسْلِم, *الْكِتَاب الْمُعَلِّم.
 */
import { article, definite, english, plain } from './alifLam'
import { TA_MARBUTA, open } from './wordForms'

const nfc = (text) => text.normalize('NFC')

/**
 * A person as one man, one woman, men and women: ة, ـُونَ, ـَات on the end. Only words that take these plurals
 * (basics.json `people`): مُسْلِمُونَ, not a broken plural like طُلَّاب. ـِينَ, the same plural elsewhere in a sentence, is not asked.
 */
export function peopleTable(person) {
  const bare = plain(person.ar)
  const one = article(person)
  return [
    { key: 'man', ar: bare, en: `${one} ${person.en} (man)` },
    { key: 'woman', ar: nfc(`${bare}َة`), en: `${one} ${person.en} (woman)` },
    { key: 'men', ar: nfc(`${bare}ُونَ`), en: `${person.many} (men)` },
    { key: 'women', ar: nfc(`${bare}َات`), en: `${person.many} (women)` },
  ]
}

/** The one-letter words joined to the front of a word with ال, and what each says. لِـ takes the place of ال's ا. */
const JOINERS = [
  { id: 'and', ar: 'وَ', en: 'and' },
  { id: 'with', ar: 'بِ', en: 'with' },
  { id: 'for', ar: 'لِ', en: 'for', drops: true },
  { id: 'like', ar: 'كَ', en: 'like' },
]

/** The word with ال, then joined to each one-letter word; wrongly, written apart (*وَ الْكِتَاب) or keeping the ا (*لِالْكِتَاب). */
export function joinedTable(word) {
  const the = definite(word.ar)
  const entries = [{ key: 'the', ar: the, en: english(word, true) }]
  for (const joiner of JOINERS) {
    entries.push({ key: joiner.id, ar: nfc(`${joiner.ar}${joiner.drops ? the.slice(1) : the}`), en: `${joiner.en} ${english(word, true)}` })
    entries.push({ key: `wrong:apart:${joiner.id}`, ar: nfc(`${joiner.ar} ${the}`), en: null })
    if (joiner.drops) entries.push({ key: `wrong:alif:${joiner.id}`, ar: nfc(`${joiner.ar}${the}`), en: null })
  }
  return entries
}

/** هٰذَا and ذٰلِكَ for a man or a masculine thing; هٰذِهِ and تِلْكَ for a feminine one. */
export const POINTERS = {
  this: { en: 'this', masculine: 'هٰذَا', feminine: 'هٰذِهِ' },
  that: { en: 'that', masculine: 'ذٰلِكَ', feminine: 'تِلْكَ' },
}

/** Whether a word is feminine as taught here: it ends in ة (basicsSkills' POINTED holds no feminine word without one). */
export const isFeminine = (word) => plain(word.ar).endsWith(TA_MARBUTA)

/**
 * "this is a book" (pointer + word without ال) and "this book" (pointer + word with ال), for this and that; then the
 * same with the pointer of the other gender, which says nothing (*هٰذِهِ كِتَاب).
 */
export function pointingTable(word) {
  const feminine = isFeminine(word)
  const forms = { is: plain(word.ar), the: definite(word.ar) }
  const entries = []
  for (const [id, pointer] of Object.entries(POINTERS)) {
    const [right, wrong] = feminine ? [pointer.feminine, pointer.masculine] : [pointer.masculine, pointer.feminine]
    const en = { is: `${pointer.en} is ${english(word, false)}`, the: `${pointer.en} ${word.en}` }
    for (const [kind, form] of Object.entries(forms)) {
      const key = kind === 'is' ? `${id}-is` : id
      entries.push({ key, ar: nfc(`${right} ${form}`), en: en[kind] })
      entries.push({ key: `wrong:gender:${key}`, ar: nfc(`${wrong} ${form}`), en: null })
    }
  }
  return entries
}

/** Who says “is” with no word for it: the pronoun, and the form of the person after it. */
const PRONOUNS = [
  { id: 'he', ar: 'هُوَ', form: 'man', en: 'he is', one: true },
  { id: 'she', ar: 'هِيَ', form: 'woman', en: 'she is', one: true },
  { id: 'they', ar: 'هُمْ', form: 'men', en: 'they are' },
  { id: 'I', ar: 'أَنَا', form: 'man', en: 'I am', one: true, hint: ' (a man speaking)' },
  { id: 'I-woman', ar: 'أَنَا', form: 'woman', en: 'I am', one: true, hint: ' (a woman speaking)' },
  { id: 'we', ar: 'نَحْنُ', form: 'men', en: 'we are' },
  { id: 'you', ar: 'أَنْتَ', form: 'man', en: 'you are', one: true, hint: ' (one man)' },
  { id: 'you-woman', ar: 'أَنْتِ', form: 'woman', en: 'you are', one: true, hint: ' (one woman)' },
  { id: 'you-all', ar: 'أَنْتُمْ', form: 'men', en: 'you are', hint: ' (all of you)' },
]

// The pronoun with the person in the wrong form, which no one says: *هُوَ مُسْلِمَة, *هِيَ مُسْلِم, *هُمْ مُسْلِم.
const DISAGREE = { he: 'woman', she: 'man', they: 'man' }

/** "he is a Muslim", "we are Muslims"…: each pronoun with the form of the person that agrees with it, then the ones that do not. */
export function pronounTable(person) {
  const forms = Object.fromEntries(peopleTable(person).map((entry) => [entry.key, entry.ar]))
  const who = (pronoun) => (pronoun.one ? `${article(person)} ${person.en}` : person.many)
  const entries = PRONOUNS.map((pronoun) => ({
    key: pronoun.id, ar: nfc(`${pronoun.ar} ${forms[pronoun.form]}`), en: `${pronoun.en} ${who(pronoun)}${pronoun.hint ?? ''}`,
  }))
  for (const [id, form] of Object.entries(DISAGREE)) {
    entries.push({ key: `wrong:agree:${id}`, ar: nfc(`${PRONOUNS.find((one) => one.id === id).ar} ${forms[form]}`), en: null })
  }
  return entries
}

/**
 * "the teacher’s book": a thing and whose it is, side by side (`pair` { thing, owner }). Beside it the same two words
 * with no ال, turned round, and said with لِـ; and as a beginner builds it wrongly, with ال on the first word too (which
 * says nothing sensible: the book is the teacher) or the first ending in -un.
 */
export function ofTable({ thing, owner }) {
  const [a, the] = [plain, definite].map((make) => ({ thing: make(thing.ar), owner: make(owner.ar) }))
  return [
    { key: 'the', ar: the.thing, en: english(thing, true) },
    { key: 'of', ar: nfc(`${a.thing} ${the.owner}`), en: `the ${owner.en}’s ${thing.en}` },
    { key: 'a', ar: nfc(`${a.thing} ${a.owner}`), en: `${article(owner)} ${owner.en}’s ${thing.en}` },
    { key: 'turned', ar: nfc(`${a.owner} ${the.thing}`), en: `the ${thing.en}’s ${owner.en}` },
    { key: 'is', ar: nfc(`${the.thing} لِ${the.owner.slice(1)}`), en: `the ${thing.en} is the ${owner.en}’s` },
    { key: 'wrong:first:of', ar: nfc(`${the.thing} ${the.owner}`), en: null },
    { key: 'wrong:tanween:of', ar: nfc(`${a.thing}\u064C ${the.owner}`), en: null },
  ]
}

/** The thing’s English for more than one: `many`, or the word with -s (basicsSkills' DUAL holds only words that take it). */
const plural = (word) => word.many ?? `${word.en}s`

/** A word, then two of it (ـَانِ), with ال or without; ـَيْنِ, the same two; and ة kept before the ending (*سَيَّارَةَانِ). */
export function dualTable(word) {
  const [a, the] = [plain(word.ar), definite(word.ar)]
  const entries = [
    { key: 'one', ar: a, en: english(word, false) },
    { key: 'the', ar: the, en: english(word, true) },
    { key: 'two', ar: nfc(`${open(a)}َانِ`), en: `two ${plural(word)}` },
    { key: 'two-yn', ar: nfc(`${open(a)}َيْنِ`), en: `two ${plural(word)}` },
    { key: 'the-two', ar: nfc(`${open(the)}َانِ`), en: `the two ${plural(word)}` },
  ]
  if (a.endsWith(TA_MARBUTA)) entries.push({ key: 'wrong:ta:two', ar: nfc(`${a}َانِ`), en: null })
  return entries
}
