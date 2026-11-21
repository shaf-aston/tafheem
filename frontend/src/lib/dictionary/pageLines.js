/**
 * A page's text cut into lines to translate one at a time.
 *
 * A book's printed lines end where the paper did, not where the sense does, so
 * a paragraph's lines are joined and cut at its full stops (entryLines' own
 * sentencesOf, the same cut the classical books get). A paragraph with no full
 * stop at all is a poem, a chat or a list of headings, and keeps its printed
 * lines. A sentence too long to read beside its English is cut where Arabic
 * itself pauses: at a comma first, then before a joining word standing on its
 * own (ثم، لكن، حتى), and only then into even pieces. Every piece is a run of the
 * page's own words in order, so nothing is lost or reordered. Lengths and the
 * joining words are dictionary.json's page block.
 */
import config from '../../config/dictionary.json'
import { blocksOf, sentencesOf } from './entryLines'
import { unvowelled } from '../text/arabicText'

const MOST = config.page['line-words']
const JOINS = new Set(config.page.joins)
const FULL_STOP = /[.؟!?]/
// After a comma, semicolon or colon, Arabic or Latin; the mark stays with the words before it.
const PAUSE = /(?<=[،؛,;:])\s+/

const wordsOf = (text) => text.split(/\s+/).filter(Boolean)

/**
 * @param {string} text the page, paragraphs apart by an empty line
 * @param {number} most the longest a line may run, in words
 * @returns {{text: string, paragraph: number}[]}
 */
export function pageLines(text, most = MOST) {
  return blocksOf(text).flatMap((part, paragraph) => {
    const pieces = FULL_STOP.test(part) ? sentencesOf(part) : part.split('\n').map((line) => line.trim()).filter(Boolean)
    return pieces.flatMap((piece) => shorter(piece, most)).map((line) => ({ text: line, paragraph }))
  })
}

/** One sentence as lines of at most `most` words, cut at its pauses first. */
export function shorter(sentence, most = MOST) {
  if (wordsOf(sentence).length <= most) return [sentence]
  return pack(sentence.split(PAUSE), most).flatMap((piece) =>
    wordsOf(piece).length <= most ? [piece] : pack(atJoins(piece), most).flatMap((part) => even(part, most)))
}

/** Pieces gathered, in order, into lines of at most `most` words; a piece already over it stands alone. */
function pack(pieces, most) {
  const lines = []
  for (const piece of pieces) {
    const last = lines.at(-1)
    if (last && wordsOf(last).length + wordsOf(piece).length <= most) lines[lines.length - 1] = `${last} ${piece}`
    else lines.push(piece)
  }
  return lines
}

/** The piece cut before every joining word that stands as a word of its own (never its first word). */
function atJoins(piece) {
  const parts = [[]]
  wordsOf(piece).forEach((word, i) => {
    if (i > 0 && JOINS.has(unvowelled(word))) parts.push([])
    parts.at(-1).push(word)
  })
  return parts.map((words) => words.join(' '))
}

/** The piece in as few even runs of at most `most` words as will hold it. */
function even(piece, most) {
  const words = wordsOf(piece)
  if (words.length <= most) return [piece]
  const count = Math.ceil(words.length / most)
  const cut = (i) => Math.round((i * words.length) / count)
  return Array.from({ length: count }, (_, i) => words.slice(cut(i), cut(i + 1)).join(' '))
}

// A word's own letters, with the marks around it (quotes, brackets, commas) apart.
const SPLIT = /^([^\p{L}\p{M}\p{N}]*)(.*?)([^\p{L}\p{M}\p{N}]*)$/u

/** The line's words, each paired with the translator's reading of it when the two agree, in order. */
export function matched(text, words) {
  let next = 0
  return text.split(/\s+/).filter(Boolean).map((token) => {
    const [, before, core, after] = token.match(SPLIT)
    const same = (word) => unvowelled(word.arabic) === unvowelled(core)
    const at = words.slice(next, next + 3).findIndex(same)
    if (at < 0) return { before, core, after }
    next += at + 1
    return { before, core, word: { ...words[next - 1], arabic: core }, after }
  })
}
