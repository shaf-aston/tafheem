/**
 * Similar verses (mutashabihat): pure helpers, no screen and no network.
 *
 * The backend marks where two twin verses differ as spans of word positions,
 * [start, end) over the ayah split on whitespace. The page works per word, so
 * spans become one flag per word here and nowhere else.
 */
import surahs from '../data/surahs.json'

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

/** A twin differing in more than this share of the verse is a thematic link, not a near-duplicate. */
export const NEAR_DUPLICATE_MAX_SHARE = 0.5

/**
 * The spans to cover for one ayah: the diff_self of its closest twin, the partner with
 * the fewest differing words (the first listed on a tie), ignoring partners that differ
 * in more than NEAR_DUPLICATE_MAX_SHARE of the verse. No such partner: no spans.
 */
export function closestSpans(text, partners = []) {
  const tokens = text.split(/\s+/).filter(Boolean)
  const real = tokens.map((token) => skeleton(token).length > 0)
  const total = real.filter(Boolean).length
  let best = null
  for (const partner of partners) {
    const flags = wordFlags(tokens.length, partner.diff_self)
    const differing = flags.filter((on, i) => on && real[i]).length
    if (differing > total * NEAR_DUPLICATE_MAX_SHARE) continue
    if (!best || differing < best.differing) best = { differing, spans: partner.diff_self }
  }
  return best ? best.spans : []
}

/** Every ayah key ("2:59") that sits in some group, from a surah's groups. */
export const twinKeys = (groups = []) => new Set(groups.flatMap((group) => group.keys))

const nameOf = (key) => surahs.find((s) => s.n === Number(key.split(':')[0]))?.en ?? key

/** Where the two verses are, in plain words. */
export function placeLine(mine, theirs) {
  const [mineSurah, mineAyah] = mine.split(':')
  const [theirSurah, theirAyah] = theirs.split(':')
  return mineSurah === theirSurah
    ? `Both are in Surah ${nameOf(mine)}, this one is ayah ${mineAyah}, that one ayah ${theirAyah}`
    : `This one is in Surah ${nameOf(mine)}, that one in Surah ${nameOf(theirs)}`
}
