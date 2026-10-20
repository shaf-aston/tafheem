/**
 * Similar verses (mutashabihat): pure helpers, no screen and no network.
 *
 * The backend marks where two twin verses differ as spans of word positions,
 * [start, end) over the ayah split on whitespace. The page works per word, so
 * spans become one flag per word here and nowhere else.
 */
import surahs from '../data/surahs.json'
import config from '../similar.json'

/** One true/false per word: is it inside any span. Spans may overlap or run past the end. */
export function wordFlags(count, spans = []) {
  const flags = Array(count).fill(false)
  for (const [start, end] of spans) {
    for (let w = Math.max(0, start); w < Math.min(count, end); w += 1) flags[w] = true
  }
  return flags
}

// A word's consonants only: the backend's text and the page's spell the same word
// differently (يَا مُوسَىٰ in two words, يَٰمُوسَىٰ in one; stand-alone pause marks), so
// words are matched by where their consonants sit, not by position.
const skeleton = (word) => word.replace(/[^\u0621-\u064A]/g, '').replace(/[\u0622\u0623\u0625\u0627]/g, '').replace(/\u0649/g, '\u064A')

/** Each word's [start, end) among the consonants of the whole text. */
function extents(words) {
  let at = 0
  return words.map((word) => { const start = at; at += skeleton(word).length; return [start, at] })
}

/**
 * One true/false per word of the page's text: does it overlap a word the backend
 * flagged. `text` is the backend's text for the same verse, `spans` over its words.
 */
export function flagsOnPage(pageWords, text, spans = []) {
  const theirs = text.split(/\s+/).filter(Boolean)
  const flagged = wordFlags(theirs.length, spans)
  const marked = extents(theirs).filter((_, i) => flagged[i])
  return extents(pageWords).map(([start, end]) => marked.some(([s, e]) => s < end && start < e))
}

const nameOf = (key) => surahs.find((s) => s.n === Number(key.split(':')[0]))?.en ?? key

/** Where the two verses are, in plain words. */
export function placeLine(mine, theirs) {
  const [mineSurah, mineAyah] = mine.split(':')
  const [theirSurah, theirAyah] = theirs.split(':')
  return mineSurah === theirSurah
    ? `Both are in Surah ${nameOf(mine)}, this one is ayah ${mineAyah}, that one ayah ${theirAyah}`
    : `This one is in Surah ${nameOf(mine)}, that one in Surah ${nameOf(theirs)}`
}

/** "{n} of {of}" filled from an object: the tab's copy keeps its numbers as names. */
export const fill = (text, values) => text.replace(/\{(\w+)\}/g, (_, name) => values[name] ?? '')

const byPlace = (a, b) => a.split(':').map(Number).reduce((d, n, i) => d || n - b.split(':').map(Number)[i], 0)

/** One id for a pair whichever verse is asked about, so its progress is filed once. */
export const pairId = (a, b) => [a, b].sort(byPlace).join('~')

const splitWords = (text) => text.split(/\s+/).filter(Boolean)

/** The words a [start, end) span holds, '' for an empty span (nothing on that side). */
export const wordsAt = (text, [start, end]) => splitWords(text).slice(start, end).join(' ')

/**
 * The questions for one pair, both ways round: each verse in turn with one of its
 * differences taken out, offered its own wording and its twin's. `changes` are the
 * backend's paired spans, `self` in `mine`. A difference longer than `maxWords` on
 * either side is left out (see similar.json), so a pair can have none.
 */
export function drillOf(mine, partner, maxWords = config['max-gap-words']) {
  const short = (span) => span[1] - span[0] <= maxWords
  const sides = [
    { verse: mine, twin: partner, own: 'self', theirs: 'other' },
    { verse: partner, twin: mine, own: 'other', theirs: 'self' },
  ]
  return sides.flatMap(({ verse, twin, own, theirs }) => (partner.changes ?? [])
    .filter((change) => short(change[own]) && short(change[theirs]))
    .map((change) => ({
      key: verse.key,
      twin: twin.key,
      words: splitWords(verse.text),
      span: change[own],
      marked: partner.changes.map((c) => c[own]),
      right: wordsAt(verse.text, change[own]),
      wrong: wordsAt(twin.text, change[theirs]),
    })))
}

/** The surah name of a key, for the copy ("Al-Baqarah 2:59"). */
export const whereOf = (key) => `${nameOf(key)} ${key}`
