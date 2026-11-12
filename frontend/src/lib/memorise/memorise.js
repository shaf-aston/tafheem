/**
 * A page of a book: what a page is, and the words of its lines. The rules for which of its
 * words go (the gaps, the choices, the marking) are components/memorise/gaps.js, which only
 * the Memorise tab uses; this file keeps what other tabs and the books borrow.
 *
 * What a page is
 * --------------
 * A mushaf page is a fact about one printing, and nothing on this machine
 * records where those pages break. So a page here is what a page is for: a
 * fixed amount of text to hold in the head at once. Whole lines are gathered
 * until about PAGE_WORDS of them have been counted, and the line that would
 * take it past is where the next page starts. A line is never cut in half,
 * because half an ayah is not something anyone memorises.
 */

import { isSpoken } from '../text/arabicText'
import config from '../../config/memorise.json'

/**
 * Every number this file works to, and nothing else. They live in
 * memorise.json, where each one is written out in words beside it, so the
 * rules below can be read as rules instead of as arithmetic. The one
 * exception says on the line above it where it lives and why.
 */
export const PAGE_WORDS = config['page-words']

/** The words of one line, as written. Splitting on spaces is all Arabic needs. */
export const wordsOf = (text) => (text ?? '').split(/\s+/).filter(Boolean)

/**
 * One ayah's place in a run of words starting at `from`. `spoken` holds the page
 * places of the words the ear scores: the server drops lone pause signs (ۖ ۚ),
 * so its scores land on these, never on `from + k`.
 */
export const ayahAt = (key, said, from) => ({
  key, from, count: said.length,
  spoken: said.flatMap((word, k) => (isSpoken(word) ? [from + k] : [])),
})

/**
 * Whole lines gathered into pages.
 *
 * Two ways, and which one is used is decided by the lines themselves rather
 * than by a setting. A line that knows its own printed page, the Qur'an's
 * ayahs do, once the Madani layout has been built; is grouped by that number,
 * and the page is then the page, not an approximation of one. Everything else
 * is gathered by word count, which is all a text with no printing of its own
 * can be sized by.
 *
 * A single line longer than a whole page is its own page rather than being
 * split, 2:282 is 128 words and is still one ayah.
 */
export function pagesOf(lines, wordsPerPage = PAGE_WORDS) {
  // Real page breaks beat any estimate, so they win whenever they are there.
  // An ayah spanning two printed pages is filed under the one it starts on:
  // half an ayah is not something anyone memorises, and a line is never split.
  if (lines.some((line) => line.page != null)) return byPrintedPage(lines)

  // Ayah lengths swing from a couple of words to over a hundred, so breaking
  // the moment a page would pass wordsPerPage leaves some pages a fraction of
  // the target, two short ayahs, then a break, because the next one wouldn't
  // fit. A page is only closed once it has already reached half the target;
  // below that it keeps pulling lines in even if the next one overshoots, so
  // "too big" loses to "too small" rather than the two trading places at random.
  const minWords = wordsPerPage / 2
  const pages = []
  let page = []
  let count = 0
  for (const line of lines) {
    const size = wordsOf(line.arabic).length
    if (page.length > 0 && count >= minWords && count + size > wordsPerPage) {
      pages.push(page)
      page = []
      count = 0
    }
    page.push(line)
    count += size
  }
  if (page.length > 0) pages.push(page)
  return pages
}

/**
 * Lines grouped by the printed page each one begins on.
 *
 * Lines missing a page number join whatever page is open, rather than starting
 * one of their own, a gap in the layout data should shorten nothing and lose
 * nothing. The pages come out in reading order because the lines arrive in it.
 */
function byPrintedPage(lines) {
  const pages = []
  let current = null
  for (const line of lines) {
    if (line.page != null && line.page !== current) {
      current = line.page
      pages.push([])
    }
    if (pages.length === 0) pages.push([])
    pages[pages.length - 1].push(line)
  }
  return pages
}

/** The printed page a page of lines sits on, or null for a word-counted one. */
export const printedPageOf = (page) => page?.find((line) => line.page != null)?.page ?? null

/**
 * A number generator the caller can reproduce, the same seed gives the same
 * page of gaps, so re-rendering never quietly moves them.
 */
export const makeRandom = (seed) => {
  let state = (seed | 0) || 1
  return () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff
    return state / 0x7fffffff
  }
}
