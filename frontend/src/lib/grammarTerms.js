/**
 * The grammar terms the app prints, read from grammar.json. Its only reader.
 *
 * A tag says the Arabic term and nothing else: مبتدأ, not "Mubtada' (مبتدأ):
 * subject of a nominal sentence. Nominative case". Someone reading nahw knows
 * the words, and someone who does not opens the glossary at the foot of the
 * page once, rather than meeting the same paragraph on every hover.
 */
import config from '../grammar.json'

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

/** A word the analyser would not name: it sends a dash rather than guess. */
export const isUnnamed = (word) => word?.role === '–'

/** The Arabic for a backend word type ("ism", "fi'l"), or the string itself. */
export const typeLabel = (key) => TYPES[key]?.arabic ?? key

/** The Arabic for a corpus part-of-speech code ("N", "V", "P"). */
export const posLabel = (tag) => typeLabel(config.corpus_pos[tag] ?? tag)

/** The glossary, in Tasheel al-Nahw's chapters; a `from` section lists the types or cases. */
export const GLOSSARY = config.sections.map(({ title, from, terms }) => ({
  title,
  terms: from ? Object.values(config[from]) : terms,
}))
