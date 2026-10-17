/**
 * A hadith split into who is talking: the words that were said, and the telling
 * around them.
 *
 * Reading a hadith as one grey block hides the thing a reader came for. The
 * books mark what was said themselves: sunnah.com puts it between quote marks,
 * in the Arabic and in the English both. So the mark is read first; only an
 * Arabic left unmarked is read from its verbs of saying instead (spoken),
 * and only colour is added: the spans joined give back the book's own text,
 * every letter and mark of it (a test holds every hadith to that).
 *
 * Quotes nest: a companion's telling sits in one quote with the Prophet's words
 * in another inside it. Only the innermost quote is `said`; a quote that holds
 * another is `told`, like everything outside quotes. Where a hadith carries no
 * quote mark at all (about one in six, mostly Muslim's English), nothing is
 * claimed: it comes back as one `plain` span.
 *
 * The one hard part is the straight ' of the English, which is three things:
 * a quote mark, an apostrophe (Allah's), and the letter ʿayn or hamza of a
 * name ('Iraq, 'Umar, Hira'). The rules, in full:
 *   1. ' between two letters is an apostrophe.
 *   2. ' (or ‘) opens a quote only where speech starts: after a colon, a comma,
 *      a dash or another quote mark (said, 'O Mughira). Anywhere else it may still be
 *      a quote (up to 'and desert the idols.'), but only if a ' closes it and
 *      more than one word sits inside: 'Ata' is a name.
 *   3. A quote mark left open when the quote around it closes was a letter,
 *      and stays in the words as one ("Once in 'Iraq, ...").
 *   4. The books sometimes close a ' quote with " (said, 'Allahu Akbar!
 *      ruined.") or a “ quote with ’; a mark closes the other kind only when
 *      the kind it is has nothing open to close.
 *
 * Pure: a string in, spans out. No React.
 */

// The chain words, owned by the server's cutter (backend/services/hadith/chain.py) and built
// into the page from the same file. This module is the page's one reader of it.
import CHAIN from '../../../backend/data/hadith/chain.json'

export { CHAIN }

// The direction marks sunnah.com sets around its marks. They are invisible
// and would otherwise be printed inside the words.
export const MARKS = /[\u200e\u200f]/g
// Each quote mark's kind and the way it faces: 1 opens, -1 closes, 0 says so by its place.
const QUOTE = {
  '“': ['double', 1], '”': ['double', -1], '"': ['double', 0],
  '‘': ['single', 1], '’': ['single', -1], "'": ['single', 0],
  '«': ['angle', 1], '»': ['angle', -1],
}
const LETTER = /[\p{L}\p{N}]/u
const SPACE = /\s/
// Where speech starts: the start, or after a colon, a comma, a dash or an opening mark.
const SPEECH = /(^|[:,“‘«"'(]|\s[-–—])\s*$/
// One word alone between ' marks is a name ('Ata'), not a saying.
const ONE_WORD = /^[\p{L}-]+\p{P}?$/u
// What a quote ends on before a mismatched closing mark: a full stop, a question,
// in the English's punctuation or the Arabic's (، ؛ ؟).
const ENDED = /[.!?,;)،؛؟]$/

/** The way a straight mark faces, from its place: 1 opens, -1 closes, 0 cannot say. */
function facing(ch, before, after) {
  if (ch === "'") {
    if (LETTER.test(before) && LETTER.test(after)) return 0
    // Before a word, or before an ellipsis or bracket that starts a quote ('..or from beneath', '(He prayed)').
    if (!LETTER.test(before) && !/[.!?,;)]/.test(before) && (LETTER.test(after) || (/[\s:(]/.test(before) && /[.([…]/.test(after)))) return 1
    return SPACE.test(before) ? 0 : -1
  }
  // After a colon a " opens even with the space on its wrong side (recited:" No soul).
  // A " before a full stop or comma closes, even with a space before it (the Arabic's  السَّاعَةِ ".).
  if (before === ':' || (SPACE.test(before) && !SPACE.test(after) && !ENDED.test(after))) return 1
  if (!SPACE.test(before) && (SPACE.test(after) || !LETTER.test(after))) return -1
  return 0
}

/** The places of the quote marks that pair up, each with its step: 1 in, -1 out. */
function quoteMarks(text) {
  const open = []   // { kind, at, speech } for each quote still open, innermost last
  const pairs = []
  let closedAt = -2   // where the last pair closed, so '" reads as two closes
  for (let at = 0; at < text.length; at += 1) {
    const ch = text[at]
    if (!QUOTE[ch]) continue
    const [kind, fixed] = QUOTE[ch]
    const before = text[at - 1] ?? ' '
    const after = text[at + 1] ?? ' '
    // A curly single between letters is ʿayn or hamza too (Ibn ‘Abbas, Aqra’).
    if (kind === 'single' && LETTER.test(before) && LETTER.test(after)) continue
    // So is one between a lone letter's full stop and a name (b.’Amir, b.'Ubaid): "b." is "bin".
    if (kind === 'single' && LETTER.test(after) && /(^|\s)\p{L}\.$/u.test(text.slice(0, at))) continue
    // A straight " that cannot say closes an open double, or else opens one.
    const step = fixed || facing(ch, before, after) || (ch === '"' ? (open.some((o) => o.kind === 'double') ? -1 : 1) : 0)
    if (step === 1) {
      open.push({ kind, at, speech: kind !== 'single' || SPEECH.test(text.slice(0, at)) })
      continue
    }
    if (step !== -1) continue
    const top = open.at(-1)
    // Rule 4: a " straight after the words of an open ' quote closes it (said, 'Allahu Akbar!
    // ruined."), unless it follows a ' that just closed: then it closes its own (?'").
    // Any ' opened inside that quote but not where speech starts was a letter ('Umar, for wheat.").
    const spoken = open.findLastIndex((o) => o.kind === 'single' && o.speech)
    const mixed = ch === '"' && spoken >= 0 && open.slice(spoken).every((o) => o.kind === 'single') && closedAt !== at - 1
    // The innermost open quote of this kind; a ' looks no further out than the nearest ".
    let i = mixed ? spoken : open.findLastIndex((o) => o.kind === kind)
    if (kind === 'single' && open.slice(i + 1).some((o) => o.kind !== 'single')) i = -1
    // A ' quote opened where speech starts outranks a ' opened inside it that may be a letter:
    // 'O Abu 'Abdur-Rahman, advise us.' closes the first.
    if (kind === 'single' && i >= 0 && !open[i].speech) {
      const spoken = open.findLastIndex((o, j) => j < i && o.kind === 'single' && o.speech)
      if (spoken >= 0 && !open.slice(spoken + 1, i).some((o) => o.kind !== 'single')) i = spoken
    }
    // Rule 4 the other way: a ’ after the words with no ' open closes the double around it.
    if (i < 0 && kind === 'single' && top && top.kind !== 'single' && ENDED.test(text.slice(0, at))) i = open.length - 1
    if (i < 0) continue   // nothing to close: the mark stays in the words
    const from = open[i]
    open.length = i   // rule 3: anything still open inside was a letter
    // Rule 2: a ' that opened where speech does not start needs a ' to close it and more than a name inside.
    if (from.kind === 'single' && !from.speech && (kind !== 'single' || !ENDED.test(text.slice(0, at)) || ONE_WORD.test(text.slice(from.at + 1, at).trim()))) continue
    pairs.push({ at: from.at, step: 1 }, { at, step: -1 })
    closedAt = at
  }
  // A double left open runs to the end, as a hadith that ends inside a saying does; a single was a letter.
  for (const o of open) if (o.kind !== 'single') pairs.push({ at: o.at, step: 1 })
  return pairs.sort((a, b) => a.at - b.at)
}

/**
 * Who says what, in order. Every span is `said`, `told` or `plain`, with the
 * book's own quote marks as `open` and `close` around its `text`; joining
 * open + text + close over every span gives back the hadith exactly, less
 * the direction marks.
 */
export function saying(text) {
  const clean = String(text ?? '').replace(MARKS, '')
  if (!clean.trim()) return []
  const marks = quoteMarks(clean)
  if (!marks.length) return [{ kind: 'plain', open: '', text: clean, close: '' }]
  const pieces = []
  let depth = 0
  let from = 0
  let opened = ''
  for (const { at, step } of marks) {
    pieces.push({ depth, open: opened, text: clean.slice(from, at), close: step < 0 ? clean[at] : '' })
    opened = step > 0 ? clean[at] : ''
    depth += step
    from = at + 1
  }
  pieces.push({ depth, open: opened, text: clean.slice(from), close: '' })
  const kept = pieces.filter((p) => p.open || p.text || p.close)
  // A quote that holds a deeper one is telling: the companion's account, not the words.
  const holds = (i) => [kept[i - 1], kept[i + 1]].some((next) => next?.depth > kept[i].depth)
  return kept.map(({ depth: d, open: o, text: t, close: c }, i) => ({ kind: d && !holds(i) ? 'said' : 'told', open: o, text: t, close: c }))
}

// A book that set no quote marks in its Arabic still says who speaks: the
// saying follows the last verb of saying (CHAIN.voice) after the body starts,
// once past who says it and to whom. Only an unmarked hadith is read this way;
// a marked one keeps saying()'s reading of its own marks.
const VOICE = new Set(CHAIN.voice.verbs)
const SPEAKER = new Set([...CHAIN.prophet, ...CHAIN.free, ...CHAIN.voice.to])
const PAST = new Set(CHAIN.voice.past)
// قال / يقول: one man speaking, whose name may go unsaid; the only verbs that can be the Prophet's.
const HE = new Set(CHAIN.voice.he)
const PROPHET = new Set(CHAIN.prophet)
// يا before رسول / النبي: speaking to the Prophet, not as him.
const CALL = new Set(CHAIN.voice.call)
// The name after بن / ابن / بنت belongs to the speaker too.
const KIN_OF = new Set(['بن', 'ابن', 'بنت'].filter((w) => CHAIN.free.includes(w)))
// A name in the raf': no ال, a dammatan on its end (أنسٌ), or a damma (عمرُ)
// on a word that does not open as a present verb does (يقولُ، تطعمُ) nor end
// in تُ (قلتُ) or هُ (دعوهُ).
const NAME = /^(?![وف]?ال)(?:\S*\u064c|[^\sيتن][\u064b-\u0652]*\S*[\u0621-\u0629\u062b-\u0647\u0649-\u064a]\u0651?\u064f)$/
// أبو هريرة، ابن عمر: a name that is two words.
const KUNYA = new Set(CHAIN.voice.kunya)
const TO_HIM = new Set(CHAIN.voice.to_him)
// The chain's last words may name him (عن النبي صلى الله عليه وسلم قال): that many count as the scene.
const CHAIN_TAIL = 8
// A full stop or question ends a sentence, and with it a saying.
const END = /[.؟?!]$/
// حدثنا، أخبرني، سمعت: a chain word, the hadith handed on (a bare حدث is a word of the saying).
const NARRATES = (word) => VERBS.has(word) && !STEMS.includes(word)

/**
 * The whole colouring of one hadith's text, as saying()'s spans:
 *   1. the book's own quote marks, where it set any (saying). The books mark
 *      the Prophet's words alone, so that is what `said` means;
 *   2. else the chain is `told`, and the body after it is read by its turns.
 *      Each verb of saying (CHAIN.voice) opens a turn; the verb and who says
 *      it stay `told`. When the Prophet says it (turn below) his words are
 *      `said` to the end of their sentence; the rest of the scene is `told`;
 *   3. a body with no word of the Prophet's tells what was done: all of it is
 *      the hadith, so all of it is `said`, the chain alone `told`.
 * `from` is where the body starts in `text`; null (no chain known) leaves an
 * unmarked text `plain`, since nothing tells chain from body.
 */
export function spoken(text, { from = null } = {}) {
  const spans = saying(text)
  if (from === null || spans.length !== 1 || spans[0].kind !== 'plain') return spans
  const clean = spans[0].text
  // `from` counts the direction marks saying() dropped.
  const body = Math.max(0, from - (String(text).slice(0, from).match(MARKS) ?? []).length)
  const words = [...clean.matchAll(/\S+/g)].map((m) => ({ at: m.index, word: bare(m[0]), raw: m[0] }))
  const first = words.findIndex((w) => w.at >= body)
  if (first < 0) return spans
  const kinds = words.map(() => 'told')
  let heard = false
  let last = null
  for (let i = first; i < words.length; i++) {
    if (!VOICE.has(words[i].word) && !NARRATES(words[i].word)) continue
    const t = turn(words, i, first, last)
    last = t
    i = t.at - 1
    if (!t.prophet) continue
    heard = true
    // His words run to the end of the sentence, or to a chain word that hands
    // the hadith on; a verb inside them is a saying he quotes.
    for (i = t.at; i < words.length && !NARRATES(words[i].word); i++) {
      kinds[i] = 'said'
      if (END.test(words[i].raw)) break
    }
  }
  if (!heard) for (let i = first; i < words.length; i++) kinds[i] = 'said'
  const out = []
  words.forEach((w, i) => {
    const start = i ? w.at : 0
    const end = words[i + 1]?.at ?? clean.length
    const last = out[out.length - 1]
    if (last?.kind === kinds[i]) last.text += clean.slice(start, end)
    else out.push({ kind: kinds[i], open: '', text: clean.slice(start, end), close: '' })
  })
  return out
}

/**
 * One turn: the verb at `verb`, who says it, and where the words start (`at`).
 * Only a verb of one man (قال، يقول; never قالت or قالوا) can be his. He says it when he is named just before the verb (أن النبي صلى الله
 * عليه وسلم قال) or just after it (قال رسول الله), or when a bare قال / يقول
 * names no one else, past the narrator's own opening verb, once he is in the
 * scene and not answering someone else named in the `last` turn, and its words
 * do not call on him (يا رسول الله).
 */
function turn(words, verb, first, last) {
  const word = (i) => words[i]?.raw.replace(/[^\p{L}\p{M}]+$/u, '') ?? ''
  let at = verb + 1
  // قال أنس / قال أبو هريرة: a past verb's subject comes next, in the raf'.
  let back = verb
  while (back > 0 && SPEAKER.has(words[back - 1].word) && !END.test(words[back - 1].raw)) back--
  const past = PAST.has(words[verb].word) && !words.slice(back, verb).some((w) => PROPHET.has(w.word))
  if (past && KUNYA.has(words[at]?.word)) at += 2
  else if (past && NAME.test(word(at))) at++
  const named = at > verb + 1
  while (at < words.length && (SPEAKER.has(words[at].word) || !LETTER.test(words[at].raw) || KIN_OF.has(words[at - 1].word))) at++
  // جاء رجل إلى النبي فقال: a Prophet the scene moves toward is not the one speaking.
  const toHim = TO_HIM.has(words[back - 1]?.word)
  const near = [...(toHim ? [] : words.slice(back, verb)), ...words.slice(verb + 1, at)]
  const calls = words.slice(at, at + 4).some((w, k, run) => CALL.has(w.word) && PROPHET.has(run[k + 1]?.word))
  // فلقيني أبو بكرة فقال، فجاءه رجلٌ فقال: someone named just before a bare verb says it.
  const namedBefore = KUNYA.has(words[back - 2]?.word) || (/^[فو]/.test(words[verb].raw) && NAME.test(word(back - 1)))
  // A bare verb is his only once he is in the scene, and not as the answer to
  // someone else just named (فقال أيوب ... قال).
  const inScene = words.slice(Math.max(0, first - CHAIN_TAIL), verb).some((w) => PROPHET.has(w.word))
  const answers = last && !last.prophet && last.named
  const bareHe = HE.has(words[verb].word) && !named && !namedBefore && verb > first + 1 && inScene && !answers
  return { verb, at, named: named || namedBefore, prophet: HE.has(words[verb].word) && (near.some((w) => PROPHET.has(w.word)) || bareHe) && !calls }
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
