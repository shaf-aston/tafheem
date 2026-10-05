/**
 * A hadith split into who is talking: the words that were said, and the telling
 * around them.
 *
 * Reading a hadith as one grey block hides the thing a reader came for. What
 * the Prophet said, what a companion saw, what happened next and who passed it
 * on are four different kinds of sentence, and the books themselves mark the
 * first one: sunnah.com puts the said words between quote marks, in the Arabic
 * and in the English both.
 *
 * So the mark is read, never guessed. A quoted stretch is `said`; everything
 * outside it is `told` and is drawn back. Where a hadith carries no quote marks
 * at all (about one in six, mostly Muslim's English), nothing is claimed: the
 * whole of it comes back as one plain span and the reader sees it in one
 * colour, which is what it looked like before any of this.
 *
 * Pure: a string in, spans out. No React.
 */

import HADITH from '../hadith.json'

// The books' own speech mark, with the direction marks sunnah.com sets around
// it. Those marks are invisible and would otherwise be printed inside the words.
const MARKS = /[‎‏]/g
const QUOTE = /["“”«»]/

/**
 * Who says what, in order. Every span is `said`, `told` or `plain`, and joining
 * their texts gives the hadith back unchanged apart from the direction marks.
 */
export function saying(text) {
  const clean = String(text ?? '').replace(MARKS, '')
  if (!clean.trim()) return []
  const pieces = clean.split(QUOTE)
  // One piece means no quote mark was found, so the books have not said which
  // part is speech and neither do we.
  if (pieces.length < 2) return [{ kind: 'plain', text: clean.trim() }]
  return pieces
    .map((piece, i) => ({ kind: i % 2 ? 'said' : 'told', text: piece.trim() }))
    .filter((span) => span.text)
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

// The chain words from hadith.json, read without vowels or punctuation.
const { verbs, endings, words: linkWords } = HADITH.chain.links
const LINKS = new Set([...linkWords, ...verbs.flatMap((verb) => endings.map((ending) => verb + ending))])
const SAYS = new Set(HADITH.chain.says)
const ABOUT = new Set(HADITH.chain.about)
const FREE = new Set(HADITH.chain.free)
// Anything but a letter goes: vowels, tatweel, direction marks, commas, colons.
const BARE = /[^\u0621-\u063A\u0641-\u064A\u0671]/g
// A quote or a bracket is the hadith's own words or a verse, never a name.
const QUOTED = /["“”«»{}()]/
// A full stop ends a sentence; a name never runs on past one.
const STOP = /[.؟!]/
const bare = (word) => {
  const plain = word.replace(BARE, '')
  const unjoined = /^[وف]/.test(plain) ? plain.slice(1) : ''
  return LINKS.has(unjoined) || SAYS.has(unjoined) ? unjoined : plain
}

/**
 * The Arabic as two parts: the chain of narrators, and the hadith it carries.
 *
 * The books do not mark where the chain ends, so it is walked, link by link:
 * a passing-on word (حدثنا، عن) then a name, until a saying word (قال، أنها)
 * that no further link follows. The hadith starts at that last saying word,
 * so "قالت النساء" keeps its verb. A name past `name` words, running on past
 * a full stop, or holding a quote, a bracket or the chain's note on itself
 * (بهذا الإسناد), or a text that does not open with a link, means the end is
 * not plain: the hadith comes back whole with an empty chain, never cut into.
 */
/** The words not set between a pair of aside marks; a mark with no partner is ignored. */
function outsideAsides(words, marks) {
  const at = marks.flatMap((mark, i) => (mark ? [i] : []))
  const inside = new Set(at.flatMap((start, k) => (k % 2 || k + 1 >= at.length ? [] : range(start, at[k + 1]))))
  return words.filter((_, i) => !inside.has(i))
}
const range = (start, end) => Array.from({ length: end - start + 1 }, (_, k) => start + k)

export function chainOf(arabic) {
  const text = String(arabic ?? '')
  const whole = { chain: '', body: text }
  const tokens = [...text.matchAll(/\S+/g)]
  const words = outsideAsides(tokens, tokens.map((m) => m[0] === HADITH.chain.aside))
    .map((m) => ({ at: m.index, word: bare(m[0]), quoted: QUOTED.test(m[0]), stop: STOP.test(m[0]) }))
    .filter((w) => w.word || w.quoted || w.stop)
  if (!LINKS.has(words[0]?.word)) return whole

  let i = 1
  while (i < words.length) {
    let name = 0
    let ended = false   // past a full stop only a link or a saying word may come
    while (i < words.length && !LINKS.has(words[i].word) && !SAYS.has(words[i].word)) {
      const { word, quoted, stop } = words[i]
      if (quoted || ABOUT.has(word) || (ended && word)) return whole
      if (word && !FREE.has(word) && ++name > HADITH.chain.name) return whole
      ended = ended || stop
      i += 1
    }
    if (i === words.length) return whole
    if (LINKS.has(words[i].word)) { i += 1; continue }
    while (i + 1 < words.length && SAYS.has(words[i + 1].word)) i += 1
    if (i + 1 < words.length && LINKS.has(words[i + 1].word)) { i += 2; continue }
    return { chain: text.slice(0, words[i].at).trim(), body: text.slice(words[i].at) }
  }
  return whole
}

// Each chain word's entry in the guide (hadith.json chain.terms): a verb by its
// stem (حدثتني is حدث), any other word whole.
const TERMS = new Map(HADITH.chain.terms.groups.flatMap(({ way, terms }) =>
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
const SPELLINGS = HADITH.chain.spellings
const keyOf = (name) => name.split(/\s+/).map(bare).filter(Boolean)
  .map((w, _, all) => (all.length > 1 && SPELLINGS[w]) || w.replace(/^ال/, '').replace(/(.{3,})ا$/, '$1').replace(/ة$/, 'ه').replace(/ى$/, 'ي'))
const KIN = new Set(HADITH.chain.kin)
const TOGETHER = new Set(HADITH.chain.together)
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
 * A chain (from chainOf) as narrators and the word that passed it between
 * each two: [{ term, way, name }], in the book's order, teacher of the author
 * first. ح starts another strand; each one but the last becomes a branch of
 * `main` (the last): `at` is the place in `main` it joins, the first narrator
 * both name, and `join` the link that names him there, for its word. No
 * narrator named in both, and `at` is null: the books do not say where that
 * strand meets (حدثني أبي names a father, not a name), so neither do we.
 */
export function chainLinks(chain) {
  const strands = [[]]
  let term = null
  let name = []
  const close = () => {
    if (name.length) strands.at(-1).push({ term: term?.word ?? '', way: term?.way ?? '', name: name.join(' ') })
    name = []
    term = null
  }
  for (const raw of String(chain ?? '').match(/\S+/g) ?? []) {
    const word = bare(raw)
    if (word === HADITH.chain.strand) { close(); strands.push([]); continue }
    if (TOGETHER.has(word)) {
      close()
      const last = strands.at(-1).at(-1)
      if (last) last.together = true
      continue
    }
    if (LINKS.has(word)) { close(); term = { word: shown(raw), way: termOf(raw)?.way ?? '' }; continue }
    if (SAYS.has(word)) { close(); continue }
    if (word) name.push(shown(raw))
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
