/**
 * How small additions change a word, for the Basics world. Pure.
 *
 * A table is every form of one word as entries { key, ar, en }:
 *   verbTable(verb)       كَتَبَتْ she wrote · سَيَكْتُبُ he will write · لَمْ يَكْتُبْ he didn't write · اُكْتُبْ Write! …
 *                         from public/grow/basics-verbs.json, whose Arabic the conjugation engine made
 *   possessiveTable(word) كِتَابُهُ his book · مَدْرَسَتِي my school …
 *   objectTable(verb)     سَمِعَهُ he heard him · سَمِعَنِي he heard me · سَمِعَنَا he heard us (and سَمِعْنَا we heard) …
 *   relativeTable(verb)   الَّذِي كَتَبَ the man who wrote · الَّتِي كَتَبَتْ the woman who wrote · الَّذِينَ كَتَبُوا those who wrote
 *   questionTable(verb)   هَلْ كَتَبَ؟ did he write? · أَكَتَبَ؟ the same · مَنْ كَتَبَ؟ who wrote? · أَيْنَ كَتَبَ؟ where did he write? …
 * plus forms a beginner builds wrongly (en null): *سَكَتَبَ, *لَمْ كَتَبَ, *الْكِتَابُهُ, *سَمِعِي. The tables of a
 * noun in a phrase (a woman, and the, this is, he is, the … of, two): lib/grow/nounForms.js.
 *
 * One spelling can say two things (تَكْتُبُ: she writes, and you write), and two spellings can say one
 * (لَمْ يَكْتُبْ and مَا كَتَبَ: he didn't write). So an option is wrong only when no reading of it is the
 * one asked: the pickers below compare readings, never keys.
 */
import { definite, plain } from './alifLam'
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

export const TA_MARBUTA = 'ة'
/** ة written ت, as it is once something follows it: مَدْرَسَة, مَدْرَسَتِي. */
export const open = (bare) => (bare.endsWith(TA_MARBUTA) ? `${bare.slice(0, -1)}ت` : bare)

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

/** The endings that say who a verb is done to: on the verb, where English puts him, her, me… after it. */
const OBJECTS = [
  { id: 'him', en: 'him', end: 'هُ' },
  { id: 'her', en: 'her', end: 'هَا' },
  { id: 'them', en: 'them', end: 'هُمْ' },
  { id: 'me', en: 'me', end: 'نِي' },
  { id: 'us', en: 'us', end: 'نَا' },
  { id: 'you', en: 'you', end: 'كَ', hint: ' (one man)' },
  { id: 'you-all', en: 'you', end: 'كُمْ', hint: ' (all of you)' },
]

/**
 * "he heard him", "he heard me"…: the past for "he" with each ending; beside them the past for "he" and "we" as they are
 * (سَمِعَنَا he heard us is سَمِعْنَا we heard but for one mark), and ـِي for "me", which is "my" on a noun (*سَمِعِي).
 */
export function objectTable(verb) {
  const { he, we } = verb.forms
  const said = (subject, rest = '') => `${subject} ${verb.en.past}${rest}`
  return [
    { key: 'he', ar: nfc(he.past), en: said('he') },
    { key: 'we', ar: nfc(we.past), en: said('we') },
    ...OBJECTS.map((object) => ({ key: object.id, ar: nfc(`${he.past}${object.end}`), en: said('he', ` ${object.en}${object.hint ?? ''}`) })),
    { key: 'wrong:ya:me', ar: nfc(`${he.past.replace(/\u064E$/, '')}\u0650ي`), en: null },
  ]
}

/**
 * "the one who…": الَّذِي, الَّتِي and الَّذِينَ, each with the verb for its person, in the past and the present; beside
 * them the past for "he" as it is. Only these: a relative word with another person's verb (الَّذِي كَتَبَتْ) is no
 * mistake but "that which she wrote", so it is never offered as one.
 */
export function relativeTable(verb) {
  const { he, she, they } = verb.forms
  const { base, past, s3 } = verb.en
  return [
    { key: 'he', ar: nfc(he.past), en: `he ${past}` },
    { key: 'the-man', ar: nfc(`الَّذِي ${he.past}`), en: `the man who ${past}` },
    { key: 'the-woman', ar: nfc(`الَّتِي ${she.past}`), en: `the woman who ${past}` },
    { key: 'those', ar: nfc(`الَّذِينَ ${they.past}`), en: `those who ${past}` },
    { key: 'the-man-now', ar: nfc(`الَّذِي ${he.present}`), en: `the man who ${s3}` },
    { key: 'those-now', ar: nfc(`الَّذِينَ ${they.present}`), en: `those who ${base}` },
  ]
}

/** The questions on a verb: `${kind}:${person}`, and مَنْ "who" for "he" only; then أَ written apart, which says nothing. */
const QUESTIONS = {
  said: { ar: (f) => f.past, en: (e, p) => `${p.subj} ${e.past}${p.hint ?? ''}` },
  did: { ar: (f) => `هَلْ ${f.past}؟`, en: (e, p) => `did ${p.subj} ${e.base}${p.hint ?? ''}?` },
  'a-did': { ar: (f) => `أَ${f.past}؟`, en: (e, p) => `did ${p.subj} ${e.base}${p.hint ?? ''}?` },
  does: { ar: (f) => `هَلْ ${f.present}؟`, en: (e, p) => `${p.s3 ? 'does' : 'do'} ${p.subj} ${e.base}${p.hint ?? ''}?` },
  what: { ar: (f) => `مَاذَا ${f.past}؟`, en: (e, p) => `what did ${p.subj} ${e.base}${p.hint ?? ''}?` },
  where: { ar: (f) => `أَيْنَ ${f.past}؟`, en: (e, p) => `where did ${p.subj} ${e.base}${p.hint ?? ''}?` },
}

export function questionTable(verb) {
  const entries = [{ key: 'who', ar: nfc(`مَنْ ${verb.forms.he.past}؟`), en: `who ${verb.en.past}?` }]
  for (const person of PERSONS) {
    const forms = verb.forms[person.id]
    for (const [kind, { ar, en }] of Object.entries(QUESTIONS)) entries.push({ key: `${kind}:${person.id}`, ar: nfc(ar(forms)), en: en(verb.en, person) })
    entries.push({ key: `wrong:apart:${person.id}`, ar: nfc(`أَ ${forms.past}؟`), en: null })
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
