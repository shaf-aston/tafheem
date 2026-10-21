/**
 * A hadith's words, read for what the page needs to draw them: where its chain
 * of narrators ends (chainAndBody), who tells the English (narrated), and the
 * chain's own words and terms (chainLinks, termOf).
 *
 * Nothing here guesses who is speaking. The page once coloured "what was said"
 * from the quote marks and verbs of saying, and got it wrong often enough to
 * mislead: a translator's note lit up as the Prophet's words, his words left
 * plain. The chain is the one split the data marks itself, so it is the only one
 * drawn; the book's own quote marks are printed as they stand.
 *
 * Pure: strings in, plain values out. No React.
 */

// The chain words, owned by the server's cutter (backend/services/hadith/chain.py) and built
// into the page from the same file. This module is the page's one reader of it.
import CHAIN from '../../../backend/data/hadith/chain.json'

export { CHAIN }

// The direction marks sunnah.com sets around its marks. They are invisible
// and would otherwise be printed inside the words.
export const MARKS = /[\u200e\u200f]/g

/**
 * One hadith as its chain and what it says, split where the server's chain reader
 * (backend chain.py, a hadith's `cut`) ends the chain: `from` is where the body
 * starts in `text`. The direction marks are dropped; joining the parts gives back
 * every other letter and mark. No `from`, no guess: the whole text is the body.
 */
export function chainAndBody(text, from = null) {
  const raw = String(text ?? '')
  const clean = raw.replace(MARKS, '')
  if (from === null) return clean ? [{ kind: 'body', text: clean }] : []
  const at = from - (raw.slice(0, from).match(MARKS) ?? []).length
  return [{ kind: 'chain', text: clean.slice(0, at) }, { kind: 'body', text: clean.slice(at) }].filter((part) => part.text)
}

// "Narrated Abu Huraira:", "It is narrated on the authority of X that ... said:"
// The books end the line that names the narrator with a colon and start the
// hadith after it, so that colon is the split rather than a guess at one.
const NARRATOR = /^([^:]{0,160}?:)\s*(.*)$/s

/** The English as two parts: who is telling it, and what they told. */
export function narrated(english) {
  const clean = String(english ?? '').replace(MARKS, '').trim()
  const match = NARRATOR.exec(clean)
  if (!match) return { narrator: '', body: clean }
  return { narrator: match[1].trim(), body: match[2].trim() }
}

/**
 * The key a reference looks up in the library's hadith map, and the name
 * sunnah.com prints for it: "muslim:157c". The letter is there when one
 * reference number covers several narrations and the event means one of them.
 */
export const hadithKey = (ref) => (ref?.hadith ? `${ref.hadith}:${ref.number}${ref.part ?? ''}` : '')

// The chain words, read without vowels or punctuation.
const { verbs, endings, words: linkWords } = CHAIN.links
// A passing-on verb with its ending (حدثه); only one hands a chain on past أن.
const VERBS = new Set(verbs.flatMap((verb) => endings.map((ending) => verb + ending)))
const LINKS = new Set([...linkWords, ...VERBS])
const SAYS = new Set(CHAIN.says)
const HANDS = new Set(CHAIN.hands)
const KIN = new Set(CHAIN.kin)
// Anything but a letter goes: vowels, tatweel, direction marks, commas, colons.
const BARE = /[^\u0621-\u063A\u0641-\u064A\u0671]/g
// A quote or a bracket is the hadith's own words or a verse, never a name.
export const QUOTED = /["“”«»{}()]/
const bare = (word) => {
  const plain = word.replace(BARE, '')
  const unjoined = /^[وف]/.test(plain) ? plain.slice(1) : ''
  return LINKS.has(unjoined) || SAYS.has(unjoined) ? unjoined : plain
}

// Each chain word's entry in the guide (CHAIN.terms): a verb by its
// stem (حدثتني is حدث), any other word whole.
const TERMS = new Map(CHAIN.terms.groups.flatMap(({ way, terms }) =>
  terms.flatMap((term) => (term.match ?? []).map((m) => [m, { ...term, way }]))))
const STEMS = [...verbs].sort((a, b) => b.length - a.length)

/** The guide's entry for one chain word as written, or null. */
export function termOf(word) {
  const plain = bare(word)
  return TERMS.get(STEMS.find((stem) => plain.startsWith(stem)) ?? plain) ?? null
}

// A name reduced to what two spellings of one narrator share: case endings,
// the article and أبو/أبا/أبي as one word (alone, أبي is "my father"). Blessings
// stay: they trail the name, so the prefix rule below reads past them, while
// dropping الله would leave عبد الله as عبد.
const SPELLINGS = CHAIN.spellings
export const keyOf = (name) => name.split(/\s+/).map(bare).filter(Boolean)
  .map((w, _, all) => (all.length > 1 && SPELLINGS[w]) || w.replace(/^ال/, '').replace(/(.{3,})ا$/, '$1').replace(/ة$/, 'ه').replace(/ى$/, 'ي'))
const TOGETHER = new Set(CHAIN.together)
// One narrator when the shorter key opens the longer (سليمان is سليمان بن يسار):
// inside one hadith's chain a name is rarely shared by two men. "My father" in
// two strands is two fathers, so it never joins them.
const same = (a, b) => {
  const [short, long] = a.length <= b.length ? [a, b] : [b, a]
  if (!short.length || (short.length === 1 && KIN.has(short[0]))) return false
  return short.every((w, i) => w === long[i])
}

// A word as printed, vowels kept, commas and direction marks gone.
const shown = (raw) => raw.replace(/[^\u0621-\u063A\u0641-\u065F\u0670\u0671]/g, '')

/**
 * A chain (the Arabic before the server's cut, lib/rijal drawnChain) as narrators and the word that passed it between
 * each two: [{ term, way, name }], in the book's order, teacher of the author
 * first, with `span`, where its name stands in `chain`. ح starts another strand; each one but the last becomes a branch of
 * `main` (the last): `at` is the place in `main` it joins, the first narrator
 * both name, and `join` the link that names him there, for its word. No
 * narrator named in both, and `at` is null: the books do not say where that
 * strand meets (حدثني أبي names a father, not a name), so neither do we.
 */
export function chainLinks(chain) {
  const strands = [[]]
  let term = null
  let name = []
  let span = null   // where the name stands in `chain`: [start, end]
  let handing = false   // the name follows أن: its verb comes after it (أن طاوسا أخبره)
  const close = () => {
    if (name.length) strands.at(-1).push({ term: term?.word ?? '', way: term?.way ?? '', name: name.join(' '), span })
    name = []
    span = null
    term = null
    handing = false
  }
  const found = [...String(chain ?? '').matchAll(/\S+/g)]
  // A remark set between two aside marks (- يعني ابن علية -) is no name; a mark with no partner is ignored.
  const marks = found.flatMap((m, i) => (m[0] === CHAIN.aside ? [i] : []))
  const inside = (i) => marks.some((from, k) => k % 2 === 0 && k + 1 < marks.length && i >= from && i <= marks[k + 1])
  for (const { 0: raw, index } of found.filter((_, i) => !inside(i))) {
    const word = bare(raw)
    if (word === CHAIN.strand) { close(); strands.push([]); continue }
    if (TOGETHER.has(word)) {
      close()
      const last = strands.at(-1).at(-1)
      if (last) last.together = true
      continue
    }
    if (LINKS.has(word)) {
      const said = { word: shown(raw), way: termOf(raw)?.way ?? '' }
      const handed = handing && name.length && VERBS.has(word)
      if (handed) term = said
      close()
      term = handed ? null : said
      continue
    }
    if (SAYS.has(word)) { close(); handing = HANDS.has(word); continue }
    if (word) { name.push(shown(raw)); span = [span?.[0] ?? index, index + raw.length] }
  }
  close()
  const [main = [], ...rest] = strands.filter((s) => s.length).reverse()
  const keys = main.map((link) => keyOf(link.name))
  // The author heard each strand from a different teacher, so the first
  // narrators never join; past them a shared name, or else the main strand's
  // "both said", is where a strand meets it.
  const together = main.findIndex((link, i) => i > 0 && link.together)
  const branches = rest.reverse().map((links) => {
    for (const [i, link] of links.entries()) {
      const at = i ? keys.findIndex((key, j) => j > 0 && same(key, keyOf(link.name))) : -1
      if (at > 0) return { links: links.slice(0, i), at, join: link }
    }
    const at = together >= 0 && together + 1 < main.length ? together + 1 : null
    return { links, at, join: at === null ? null : main[at] }
  })
  return { main, branches }
}

/**
 * Which hadiths each part of one event prints, so none is printed twice.
 *
 * One long hadith often tells a whole run: the fall of Constantinople and the
 * two steps inside it are all one narration, and printing it under the event
 * and again under each step is the same page of Arabic three times over. The
 * first place that cites it prints it; everything below says the number and
 * leaves the words to the copy above.
 *
 * Keyed by step id, with the event itself under the empty string.
 */
export function printedBy(event) {
  const seen = new Set()
  const byPart = new Map()
  const take = (id, refs) => {
    const keys = (refs ?? []).map(hadithKey).filter((key) => key && !seen.has(key))
    for (const key of keys) seen.add(key)
    byPart.set(id, new Set(keys))
  }
  const walk = (steps) => {
    for (const step of steps ?? []) {
      take(step.id, step.refs)
      walk(step.steps)
    }
  }
  take('', event?.refs)
  walk(event?.steps)
  return byPart
}
