/**
 * Lane's lexicon, from one run-on paragraph into the shape it was printed in.
 *
 * Lane's book is set like a book: a heading for each verb form, a numbered
 * sense under it, lettered sub-senses under that, and the authorities in
 * brackets after every claim. The text we hold keeps all of that, but as marks
 * inside one string, so the browser draws twenty column-inches of unbroken
 * grey. The entry is not hard to read because Lane wrote it densely; it is hard
 * to read because its structure was flattened. This puts it back.
 *
 * What the marks are, all of them from the Perseus edition:
 *   1 نَارَ         a verb form heading, the digit being the form number
 *   -A2-           the next distinct sense of that form
 *   ― -b2-         a sub-sense of the sense above
 *   (S, A, Msb, K.) the authorities, present on nearly every clause
 *   [ ... ]        Lane's own aside, not the Arab lexicographers'
 *   (tropical:)    the figurative-sense tag
 *   ا^َنَارَ         one word split by a stray ^ or @, an artifact of the dump
 *   شَا=ءَهُ         the same, but split at a lost hamza; = is the more common
 *                  of the two, 13,764 against 3,822 for ^ and @ together
 *
 * Pure: a string in, a list of blocks out. Nothing here knows about React, and
 * the numbers below are the book's own, never invented here. A block whose
 * markers are absent comes back as one plain block, so a book that does not
 * use this markup passes through unharmed.
 */

// The bidi isolates the dump wraps every Arabic run in. Kept in the output,
// since they are what stops an Arabic word reordering the English around it.
const FSI = '⁨'
const PDI = '⁩'

// A word the dump broke in two: ^ and @ where the halves are simply adjacent,
// = where the second half opens with a hamza the dump lost. Only matched
// between two Arabic runs, so a real caret or equals sign elsewhere in the
// prose (e.g. "the sign =") is never touched.
const WORD_SPLIT = new RegExp(`${PDI}[\\^@=]${FSI}`, 'g')
// An = after an alif and before any letter but hamza is the madda the dump
// could not write: ا=بَ is آبَ and مَا=بٌ is مَآبٌ, about 2,900 times. Before a
// hamza (10,758) the hamza is already there, شَا=ءَ is شَاءَ, so only the join.
const MADDA_SPLIT = new RegExp(`ا${PDI}=${FSI}(?!ء)`, 'g')

// A verb form heading: a digit alone between the end of a sentence and an
// Arabic run. Anchored that tightly because Lane's prose is full of loose
// digits, "see 4, in two places" and "the Kur, vi. 1" among them, and a
// heading invented mid-sentence would break the entry rather than set it.
const FORM = new RegExp(`(?:^|(?<=[.:)\\]${PDI}]\\s))(\\d{1,2}) (?=${FSI})`, 'g')

// -A2- opens a sense, ― -b2- a sub-sense. The dash before -b is Lane's own
// paragraph mark and goes with it.
const SENSE = /―?\s*-([Ab])(\d+)-\s*/g

// The authorities, and Lane's asides. Both are true parentheses in the text,
// so they are matched as a whole and marked rather than parsed.
const CITE = /\([^()]{0,40}\)|\[[^[\]]{0,300}\]/g
const TROPICAL = /\(tropical:\)/

// A verse: "in the Kur [lvi. 9]", "in the Kur xii. 68", the roman numeral the
// sura and the digit the verse. The word Kur in front is what makes the swap
// safe. Lane numbers Baydawi's commentary and Freytag's proverbs the same way,
// 1,332 times in the book against 2,867 verses, and "Arab. Prov. ii. 119" is
// not sura 2. Matched before CITE so the brackets around one go to it first.
const KUR = /Kur(?:-án)?,?\s*(?:ch\.\s*)?(\[[^[\]]{0,60}\](?:\s*(?:and\s+)?[ivxlc]{1,8}\.\s*\d+)?|[ivxlc]{1,8}\.\s*\d+)/
const VERSE = /\b([ivxlc]{1,8})\.\s*(\d+)/g
const MARKS = new RegExp(`${KUR.source}|${CITE.source}`, 'g')
// The same rule again, for the verses quoted inside one of Lane's own asides:
// "[in the Kur ii. 5, meaning ...]" is matched whole as an aside, so the verse
// in it is never reached by the scan above. 614 of the book's 2,900.
const KUR_INSIDE = new RegExp(KUR.source, 'g')
const ROMAN = { i: 1, v: 5, x: 10, l: 50, c: 100 }

/** A roman numeral as a number, 0 if the letters do not make one. */
function roman(numeral) {
  let total = 0
  for (let at = 0; at < numeral.length; at += 1) {
    const here = ROMAN[numeral[at]]
    const next = ROMAN[numeral[at + 1]]
    total += next > here ? -here : here
  }
  return total
}

/**
 * "the Kur [lvi. 9]" as "Qur'án 56:9", the way anyone would look it up.
 *
 * The whole match comes back untouched unless a sura in range comes out of it,
 * so a numeral Lane wrote for something else is never rewritten into a verse.
 */
function verseRef(match, cited) {
  const said = cited.replace(/[[\]]/g, '').replace(VERSE, (all, numeral, verse) => {
    const sura = roman(numeral)
    return sura >= 1 && sura <= 114 ? `${sura}:${verse}` : all
  })
  return /\d+:\d+/.test(said) ? `Qur'án ${said}` : match
}

// A tatweel straight after an alif, 12,078 times in Lane and in no other book
// on the shelf. It is the Perseus dump's carrier for a hamzated alif and it
// draws as a bar through the word: اـِذَا. The bar goes; the hamza is not put
// back, because which of أ or إ was meant is not written down here and the app
// never guesses a spelling.
const STRAY_TATWEEL = /(?<=ا)ـ/g

// An authority list, the (S, Mgh, * Msb, K) after nearly every clause: each
// item a capitalised abbreviation or name. A lowercase word inside means prose,
// so (tropical:) and (he said so) are never taken for one. "&c." closes a list
// as "and the rest", 10,470 times.
const AUTHORITY = /^(?:&c|[A-Z][\w'-]*\.?(?:\s+[A-Z][\w'-]*\.?){0,2})$/
// A source by its capitals alone, T or TA, safe to take out even when it is the
// only one beside prose: "(an absent person, T)". I is the pronoun, not a source.
const ABBREVIATION = /^(?!I$)[A-Z]{1,4}$/

const itemsOf = (inner) => inner.replace(/[*†]/g, ' ').split(/[,;]/)
  .map((item) => item.trim().replace(/[.:]$/, '')).filter(Boolean)

function isAuthorities(paren) {
  if (!paren.startsWith('(')) return false
  const items = itemsOf(paren.slice(1, -1))
  return items.length > 0 && items.every((item) => AUTHORITY.test(item))
}

/**
 * A parenthesis with the authorities taken out: gone when nothing else was in
 * it, otherwise what remains. "(طَرِيق, Mgh, Msb, TA)" keeps its word. Only
 * trimmed when two or more items look like authorities, or the only one is an
 * abbreviation, so a lone capitalised word in real prose is never read as one.
 */
function withoutAuthorities(paren) {
  if (isAuthorities(paren)) return ''
  const items = itemsOf(paren.slice(1, -1))
  const dropped = items.filter((item) => AUTHORITY.test(item))
  const trim = dropped.length >= 2 || (dropped.length === 1 && ABBREVIATION.test(dropped[0]))
  return trim ? `(${items.filter((item) => !dropped.includes(item)).join(', ')})` : paren
}

// Lane ends a statement with its sources and a colon, "(M, TA:)", and the next
// alternative follows: "or ...", "and ...". In the clean view that list becomes
// the paragraph break it marks, so a 10,000-character sense is not one block.
const CLAUSE_END = /(:?)\s*(\([^()]{0,60}:\))\s*/g
const breakClauses = (text) => text.replace(CLAUSE_END, (all, colon, paren) => (
  isAuthorities(paren) ? ':\n' : all))

// Lane sometimes opens his own note inside the authority list, before the
// bracket closes: "(Mgh, Msb, * K. * [It is said in the TA ...])". The note is
// kept and the list around it goes. Safe to run before the entry is cut, since
// it never touches a heading or a verse. The closing ")" is optional because
// the dump sometimes drops it, as it does in the entry on شرك.
const NOTE_IN_LIST = /\(([^()[\]]{0,60}?)\s*(\[[^[\]]*\])(?:\s*\))?/g
const liftNotes = (text) => text.replace(NOTE_IN_LIST, (all, list, note) => (
  isAuthorities(`(${list})`) ? note : all))

// "He (God) created him": a name straight after a personal pronoun says who is
// meant, not who reported it. 166 in the book, "He (God)" 125 of them.
const PRONOUN = /\b(?:[Hh]e|[Ss]he|[Hh]is|[Hh]er)\s$/
const PAREN = /\([^()]{0,60}\)/g

/** Whether a whole-name parenthesis is kept, given the text before it. */
const namesPronoun = (paren, before) => isAuthorities(paren) && PRONOUN.test(before)

// Lane's pointers for a reader holding the printed book: ↓ and * mark a word
// treated elsewhere, "q. v." and "infrà" say where. On screen they point nowhere.
const POINTERS = [
  [/[^\S\n]*↓[^\S\n]*/g, ' '],
  [/(^|\s)\*(?=\s|$)/g, '$1'],
  [/\bq\.\s?v\.,?/g, ''],
  // No \b after the à: JavaScript counts it as a non-word letter.
  [/\b(?:infr|supr)à/g, ''],
  [/\[\s*[,;.]?\s*\]/g, ''],
  // "[&c.:]", Lane's "and the rest" with nothing before it.
  [/\[\s*&c\.?[,;:.]?\s*\]/g, ''],
]

/**
 * Lane's prose without the scholar's apparatus: authority lists and pointers
 * gone, the spaces and commas they leave behind mended. The meaning, Lane's own
 * bracketed English and the verses all stay. Only ever a view; the stored
 * entry keeps every mark.
 */
export function tidyNotes(text) {
  let out = liftNotes(text).replace(PAREN, (paren, at, whole) => (
    namesPronoun(paren, whole.slice(0, at)) ? paren : withoutAuthorities(paren)))
  for (const [mark, to] of POINTERS) out = out.replace(mark, to)
  return out
    .replace(/[^\S\n]{2,}/g, ' ')
    .replace(/[^\S\n]+([,;:.\]])/g, '$1')
    .replace(/([,;:])(?:\s*[,;:])+/g, '$1')
    .replace(/\[\s+/g, '[')
}

/** The dump splits a word at a stray ^, @ or =; all three mean "one word". */
export function mendWords(text) {
  return text
    .replace(MADDA_SPLIT, 'آ')
    .replace(WORD_SPLIT, '')
    .replace(STRAY_TATWEEL, '')
}

/**
 * The same entry for a place that prints it as prose rather than setting it
 * out. Daleel quotes whole entries beside an ayah, and the dump's own marks,
 * the "― -b2-" that opens a sub-sense among them, were left on screen as
 * litter. Each becomes the line break it stands for.
 */
export function plainEntry(text, { tidy = false } = {}) {
  let said = mendWords(text ?? '')
  // Tidy also starts each verb form on its own line, where the book starts it.
  if (tidy) said = tidyNotes(breakClauses(said.replace(FORM, '\n$1 ')))
  // The space in front of the mark is the one the sentence ended with, and it
  // would otherwise be left hanging at the end of a line.
  return said.replace(SENSE, '\n').replace(/[^\S\n]+\n/g, '\n').trim()
}

/**
 * One block's prose, cut into the runs that get drawn differently.
 *
 * Tidied after the cut, not before: headings and verses are found on the text
 * as printed, and an authority is dropped whole. Neighbouring prose is joined
 * first so the space and comma either side of a dropped list mend as one.
 */
function pieces(text, tidy) {
  if (!tidy) return cutPieces(text)
  const cut = cutPieces(liftNotes(text))
  const joined = []
  for (const found of cut) {
    const last = joined.at(-1)
    let piece = found
    // A bracket with nothing left once tidied, "[&c.:]", goes before the join
    // so the punctuation either side of it mends as one.
    if (piece.kind === 'cite' && piece.text.startsWith('[') && !tidyNotes(piece.text)) continue
    if (piece.kind === 'cite' && isAuthorities(piece.text)) {
      // A name after a pronoun is part of the sentence, so it reads as prose.
      if (!namesPronoun(piece.text, last?.text ?? '')) continue
      piece = { ...piece, kind: 'text' }
    }
    if (piece.kind === 'text' && last?.kind === 'text') last.text += piece.text
    else joined.push({ ...piece })
  }
  return joined
    .map((piece) => (piece.kind === 'ref' || piece.kind === 'tag'
      ? piece : { ...piece, text: tidyNotes(piece.text) }))
    .filter((piece) => piece.text)
}

function cutPieces(text) {
  const out = []
  let at = 0
  for (const found of text.matchAll(MARKS)) {
    if (found.index > at) out.push({ kind: 'text', text: text.slice(at, found.index) })
    if (found[1] !== undefined) {
      // A verse, unless the numeral turned out not to be a sura, in which case
      // it goes back into the prose exactly as Lane wrote it.
      const ref = verseRef(found[0], found[1])
      out.push({ kind: ref === found[0] ? 'text' : 'ref', text: ref })
    } else {
      // A tropical tag is a label on the sense, not an authority, and is the
      // one parenthesis a reader is meant to notice rather than skim past.
      out.push({
        kind: TROPICAL.test(found[0]) ? 'tag' : 'cite',
        text: found[0].replace(KUR_INSIDE, verseRef),
      })
    }
    at = found.index + found[0].length
  }
  if (at < text.length) out.push({ kind: 'text', text: text.slice(at) })
  // Only genuinely empty runs go. A run of one space is the gap between two
  // brackets, and dropping it ran "(Mgh, Msb:)" straight into "(tropical:)".
  return out.filter((piece) => piece.text)
}

/**
 * The senses and sub-senses inside one verb form, in the order printed. In the
 * clean view a sense runs on in unnumbered paragraphs, number 0, one per
 * statement.
 */
function senses(text, tidy) {
  const out = []
  let at = 0
  let kind = 'sense'
  let number = 1
  const push = (end) => {
    const body = text.slice(at, end).trim()
    const paragraphs = (tidy ? breakClauses(body) : body).split('\n')
      .map((part) => part.trim()).filter(Boolean)
    paragraphs.forEach((part, i) => out.push({ kind, number: i ? 0 : number, pieces: pieces(part, tidy) }))
  }
  for (const found of text.matchAll(SENSE)) {
    push(found.index)
    kind = found[1] === 'A' ? 'sense' : 'sub'
    number = Number(found[2])
    at = found.index + found[0].length
  }
  push(text.length)
  return out
}

// The Arabic word a section opens with, and the punctuation after it. Capped so
// an Arabic sentence is never lifted into a heading.
const LEAD_WORD = new RegExp(`^${FSI}([^${FSI}${PDI}]{1,30})${PDI}[\\s,;:]*`)

const HARAKAT = /[ً-ْ]/g

/**
 * The heading word without the unvowelled copy the dump prints after it:
 * "مَآبٌ مآب" is one word, "رِيحٌ مُؤْوِبَةٌ" is a phrase and stays whole.
 */
function headingWord(run) {
  const [first, ...rest] = run.trim().split(/\s+/)
  const bare = first.replace(HARAKAT, '')
  return [first, ...rest.filter((word) => word !== bare)].join(' ')
}

/** A section: its opening word lifted out as the heading, the rest as senses. */
function section(form, raw, tidy) {
  const found = raw.match(LEAD_WORD)
  const text = found ? raw.slice(found[0].length) : raw
  return { form, word: found ? headingWord(found[1]) : null, senses: senses(text, tidy) }
}

/**
 * One headword: the verb form or the noun, and everything said under it.
 *
 * A book with no form headings comes back as a single form with no number, so
 * the caller has one shape to draw either way.
 */
function headword(raw, tidy) {
  const text = raw.trim()
  if (!text) return []

  const heads = [...text.matchAll(FORM)]
  if (!heads.length) return [section(null, text, tidy)]

  const forms = []
  // Anything before the first heading is the root's own headword line.
  const lead = text.slice(0, heads[0].index).trim()
  if (lead) forms.push(section(null, lead, tidy))

  heads.forEach((head, i) => {
    const from = head.index + head[0].length
    const to = i + 1 < heads.length ? heads[i + 1].index : text.length
    forms.push(section(head[1], text.slice(from, to).trim(), tidy))
  })
  return forms
}

/**
 * The whole entry, headword by headword.
 *
 * Each line is one headword, because the book itself broke the paragraph
 * there: Perseus opens an element at every one, and the builder keeps that
 * break as a line. Nothing here has to guess where a new word starts, which is
 * the one thing no rule about Lane's wording could do safely.
 */
export function laneEntry(raw, { tidy = false } = {}) {
  return mendWords(raw ?? '').split('\n').flatMap((line) => headword(line, tidy))
}
