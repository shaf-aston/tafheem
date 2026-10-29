/**
 * How small additions change a word, for the Basics world. Pure.
 *
 * A table is every form of one word as entries { key, ar, en }:
 *   verbTable(verb)       كَتَبَتْ she wrote · سَيَكْتُبُ he will write · لَمْ يَكْتُبْ he didn't write · اُكْتُبْ Write! …
 *                         from public/grow/basics-verbs.json, whose Arabic the conjugation engine made
 *   possessiveTable(word) كِتَابُهُ his book · مَدْرَسَتِي my school …
 *   peopleTable(person)   مُسْلِم · مُسْلِمَة · مُسْلِمُونَ · مُسْلِمَات: a man, a woman, men, women
 *   joinedTable(word)     وَالْكِتَاب and the book · بِالْقَلَم with the pen · لِلْبَيْت for the house · كَالْقَمَر like the moon
 *   pointingTable(word)   هٰذَا كِتَاب this is a book · هٰذَا الْكِتَاب this book · تِلْكَ سَيَّارَة that is a car …
 * plus forms a beginner builds wrongly (en null): *سَكَتَبَ, *لَمْ كَتَبَ, *الْكِتَابُهُ, *وَ الْكِتَاب, *هٰذِهِ كِتَاب.
 *
 * One spelling can say two things (تَكْتُبُ: she writes, and you write), and two spellings can say one
 * (لَمْ يَكْتُبْ and مَا كَتَبَ: he didn't write). So an option is wrong only when no reading of it is the
 * one asked: the pickers below compare readings, never keys.
 */
import { article, definite, english, plain } from './alifLam'
import { shuffled } from '../text/shuffle'

const nfc = (text) => text.normalize('NFC')

/** The persons a beginner meets first (هو هي هم أنتَ أنتم أنا نحن), in basics-verbs.json's order. */
export const PERSONS = [
  { id: 'he', subj: 'he', s3: true },
  { id: 'she', subj: 'she', s3: true },
  { id: 'they', subj: 'they' },
  { id: 'you', subj: 'you', hint: ' (one man)' },
  { id: 'you-all', subj: 'you all' },
  { id: 'I', subj: 'I' },
  { id: 'we', subj: 'we' },
]
export const ADDRESSED = ['you', 'you-all']

const capital = (text) => text[0].toUpperCase() + text.slice(1)
const said = (person) => (person.id === 'you' ? ' (one man)' : ' (all of you)')

/** Each tense: its Arabic from the person's forms, its English from the verb's three English forms. */
export const TENSES = {
  past: { ar: (f) => f.past, en: (e, p) => `${p.subj} ${e.past}${p.hint ?? ''}` },
  present: { ar: (f) => f.present, en: (e, p) => `${p.subj} ${p.s3 ? e.s3 : e.base}${p.hint ?? ''}` },
  future: { ar: (f) => `سَ${f.present}`, en: (e, p) => `${p.subj} will ${e.base}${p.hint ?? ''}` },
  'future-sawfa': { ar: (f) => `سَوْفَ ${f.present}`, en: (e, p) => `${p.subj} will ${e.base}${p.hint ?? ''}` },
  not: { ar: (f) => `لَا ${f.present}`, en: (e, p) => `${p.subj} ${p.s3 ? 'doesn’t' : 'don’t'} ${e.base}${p.hint ?? ''}` },
  'not-past': { ar: (f) => `لَمْ ${f.juss}`, en: (e, p) => `${p.subj} didn’t ${e.base}${p.hint ?? ''}` },
  'not-past-ma': { ar: (f) => `مَا ${f.past}`, en: (e, p) => `${p.subj} didn’t ${e.base}${p.hint ?? ''}` },
  'not-future': { ar: (f) => `لَنْ ${f.subj}`, en: (e, p) => `${p.subj} won’t ${e.base}${p.hint ?? ''}` },
  command: { only: ADDRESSED, ar: (f) => f.command, en: (e, p) => `${capital(e.base)}!${said(p)}` },
  prohibit: { only: ADDRESSED, ar: (f) => `لَا ${f.juss}`, en: (e, p) => `Don’t ${e.base}!${said(p)}` },
}

/** A particle on the wrong tense, or written apart: forms that say nothing. */
export const WRONG_VERB = {
  'sa-past': (f) => `سَ${f.past}`,
  'sa-apart': (f) => `سَ ${f.present}`,
  'sawfa-past': (f) => `سَوْفَ ${f.past}`,
  'lam-past': (f) => `لَمْ ${f.past}`,
  'lan-past': (f) => `لَنْ ${f.past}`,
}

/** Every form of one verb: `${tense}:${person}`, then `wrong:${kind}:${person}` with no English. */
export function verbTable(verb) {
  const entries = []
  for (const person of PERSONS) {
    const forms = verb.forms[person.id]
    for (const [tense, { only, ar, en }] of Object.entries(TENSES)) {
      if (only && !only.includes(person.id)) continue
      entries.push({ key: `${tense}:${person.id}`, ar: nfc(ar(forms)), en: en(verb.en, person) })
    }
    for (const [kind, ar] of Object.entries(WRONG_VERB)) entries.push({ key: `wrong:${kind}:${person.id}`, ar: nfc(ar(forms)), en: null })
  }
  return entries
}

/** The endings that say whose: on the noun, where English puts my, your, his… before it. */
export const POSSESSORS = [
  { id: 'my', en: 'my', end: 'ِي' },
  { id: 'your', en: 'your', end: 'ُكَ', hint: ' (one man)' },
  { id: 'his', en: 'his', end: 'ُهُ' },
  { id: 'her', en: 'her', end: 'ُهَا' },
  { id: 'our', en: 'our', end: 'ُنَا' },
  { id: 'your-all', en: 'your', end: 'ُكُمْ', hint: ' (all of you)' },
  { id: 'their', en: 'their', end: 'ُهُمْ' },
]

const TA_MARBUTA = 'ة'
// ة is written ت once something follows it: مَدْرَسَة, مَدْرَسَتِي.
const open = (bare) => (bare.endsWith(TA_MARBUTA) ? `${bare.slice(0, -1)}ت` : bare)

// أَب and أَخ lengthen before an ending (أَبُوهُ his father), so the plain rule does not hold for them.
const LENGTHEN = new Set(['أب', 'أخ'])
const letters = (text) => text.replace(/[\u064B-\u0652\u0670]/g, '')

/**
 * Whether a word takes the endings as they are taught here: it ends on a plain consonant or ة.
 * Not a long vowel or hamza (عَصَا, سَمَاء, whose hamza changes its seat), a doubled letter (كُرْسِيّ), or أَب/أَخ.
 */
export const canPossess = (word) => {
  const bare = plain(word.ar)
  return !/(?:[اىءأإؤئوي]|\u0651)$/.test(bare) && !LENGTHEN.has(letters(bare))
}

/** Every "whose" form of one noun, then the wrong ones: ال with an ending (*الْكِتَابُهُ), ة left as it is (*مَدْرَسَةُهُ). */
export function possessiveTable(word) {
  const bare = plain(word.ar)
  const entries = []
  for (const owner of POSSESSORS) {
    entries.push({ key: `mine:${owner.id}`, ar: nfc(`${open(bare)}${owner.end}`), en: `${owner.en} ${word.en}${owner.hint ?? ''}` })
    // ال with ـِي can read as a real word (الْجَارِي the flowing, الْقَلْبِي of the heart), unless the ة shows it is not one.
    if (owner.id !== 'my' || bare.endsWith(TA_MARBUTA)) entries.push({ key: `wrong:al:${owner.id}`, ar: nfc(`${open(definite(bare))}${owner.end}`), en: null })
    if (bare.endsWith(TA_MARBUTA)) entries.push({ key: `wrong:ta:${owner.id}`, ar: nfc(`${bare}${owner.end}`), en: null })
  }
  return entries
}

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
export const JOINERS = [
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

/** Each spelling in the table and everything it can mean. */
export function meanings(entries) {
  const byAr = new Map()
  for (const { ar, en } of entries) {
    if (!byAr.has(ar)) byAr.set(ar, new Set())
    if (en) byAr.get(ar).add(en)
  }
  return byAr
}

const entryOf = (entries, key) => entries.find((entry) => entry.key === key)
const distinct = (list, by) => list.filter((one, i) => list.findIndex((other) => by(other) === by(one)) === i)

/**
 * "Which one is ‘she wrote’?": the asked form and up to `n` from `pool` (keys), none of which can mean what was asked.
 * Options: { id: 'right' | key, text }.
 */
export function arabicOptions(entries, key, pool, random, n = 2) {
  const asked = entryOf(entries, key)
  const byAr = meanings(entries)
  const wrong = distinct(
    pool.map((one) => entryOf(entries, one)).filter((one) => one && one.ar !== asked.ar && !byAr.get(one.ar).has(asked.en)),
    (one) => one.ar,
  )
  const picked = shuffled(wrong, random).slice(0, n)
  return shuffled([{ id: 'right', text: asked.ar }, ...picked.map((one) => ({ id: one.key, text: one.ar }))], random)
}

/** "What does سَيَكْتُبُ mean?": its meaning and up to `n` meanings from `pool` that the shown form cannot have. */
export function englishOptions(entries, key, pool, random, n = 2) {
  const shown = entryOf(entries, key)
  const readings = meanings(entries).get(shown.ar)
  const wrong = distinct(
    pool.map((one) => entryOf(entries, one)).filter((one) => one?.en && !readings.has(one.en)),
    (one) => one.en,
  )
  const picked = shuffled(wrong, random).slice(0, n)
  return shuffled([{ id: 'right', text: shown.en }, ...picked.map((one) => ({ id: one.key, text: one.en }))], random)
}
