/**
 * The grammar terms the app prints, read from grammar.json. Its only reader.
 *
 * A tag leads with the Arabic term, مبتدأ, and two or three words of English under
 * it ("topic"), not "Mubtada' (مبتدأ): subject of a nominal sentence. Nominative
 * case": a learner is not left guessing what the tag names, and what it means in
 * full is in the glossary at the foot of the page, once, not on every word.
 */
import config from '../../config/grammar.json'
import { unvowelled } from '../text/arabicText'

const CASES = config.cases
const TYPES = config.types

/**
 * The Arabic for a backend case string, or the string itself if unknown.
 * "mabni (سكون على اللام)": the first word is the case, the rest is its fixed
 * harakah and stays as written.
 */
export const caseLabel = (key) => {
  const [head, ...rest] = String(key ?? '').split(' ')
  const term = CASES[head]?.arabic
  return term ? [term, ...rest].join(' ') : key
}

/** What the analyser sends for a word it would not name, or a cell with nothing in it. */
export const UNNAMED = '–'

/** A word the analyser would not name: it sends a dash rather than guess. */
export const isUnnamed = (word) => word?.role === UNNAMED

/**
 * A word's case and sign as one reading, the pieces to print in order: a sign that
 * already opens with the case (مبني على الفتح) is not said twice (مبني · مبني على الفتح).
 * The table and the copied text both print it through here, so they never differ.
 */
export const reading = (word) => {
  const c = word.case ? caseLabel(word.case) : ''
  return word.sign?.startsWith(c) ? [word.sign] : [c, word.sign].filter(Boolean)
}

/** The Arabic for a backend word type ("ism", "fi'l"), or the string itself. */
export const typeLabel = (key) => TYPES[key]?.arabic ?? key

/** The Arabic for a corpus part-of-speech code ("N", "V", "P"). */
export const posLabel = (tag) => typeLabel(config.corpus_pos[tag] ?? tag)

/** The glossary, in Tasheel al-Nahw's chapters; a `from` section lists the types or cases first, then its own terms. */
export const GLOSSARY = config.sections.map(({ title, from, terms }) => ({
  title,
  terms: [...(from ? Object.values(config[from]) : []), ...(terms ?? [])],
}))

/** The word a word takes its case from, as an index: its عامل, or the word a تابع follows. Undefined for neither. */
export const caseFrom = (word) => word.governor ?? word.follows ?? undefined

// The roles' English, keyed by spelling alone: the analyser writes a role fully vowelled (نَائِبُ فَاعِلٍ).
const ROLE_EN = new Map(Object.entries(config.roles).filter(([key]) => !key.startsWith('_')).map(([ar, en]) => [unvowelled(ar), en]))

/**
 * A role in two or three English words, or '' for one not listed. A role named for a sister
 * of كان or إن (خبر ليس، اسم كأن) is not each listed: it is said by its job, "news" or "subject".
 */
export const roleGloss = (role) => {
  const plain = unvowelled(String(role ?? '').trim())
  if (ROLE_EN.has(plain)) return ROLE_EN.get(plain)
  const job = plain.split(' ')[0]
  return job === 'اسم' && plain.includes(' ') ? 'subject' : job === 'خبر' ? ROLE_EN.get(job) : ''
}

/** A backend case string's English ("nominative"), or ''. */
export const caseGloss = (key) => CASES[String(key ?? '').split(' ')[0]]?.en ?? ''

/** A backend word type's English ("noun"), or ''. */
export const typeGloss = (key) => TYPES[key]?.en ?? ''

/** A corpus part-of-speech code's English ("noun"), or ''. */
export const posGloss = (tag) => typeGloss(config.corpus_pos[tag] ?? tag)
