/**
 * Fill in the gaps: a page of a book with some of its words taken out.
 *
 * What a page is
 * --------------
 * A mushaf page is a fact about one printing, and nothing on this machine
 * records where those pages break. So a page here is what a page is for: a
 * fixed amount of text to hold in the head at once. Whole lines are gathered
 * until about PAGE_WORDS of them have been counted, and the line that would
 * take it past is where the next page starts. A line is never cut in half,
 * because half an ayah is not something anyone memorises.
 *
 * Which words go
 * --------------
 * Not a coin flip per word. Two things make a gap worth filling:
 *   - the line still starts with its own first word, which is the cue the
 *     memory hangs on. Blank that and the reader is guessing, not recalling.
 *   - two gaps never sit side by side while little enough of a line is hidden
 *     for that to be possible, because a run of blanks is one hard gap rather
 *     than two fair ones. Past that share the rule steps aside rather than
 *     quietly hiding fewer words than asked; see spacing-drops-at-share.
 * Inside those two rules the choice is random, from a seed the caller owns, so
 * the same page can be handed back identically or reshuffled on demand.
 *
 * Judging an answer
 * -----------------
 * Nobody filling in a gap types the vowel marks, and the Qur'anic printing uses
 * marks a keyboard has no key for at all. Those are folded away, and where the
 * printing and later spelling differ by a whole letter rather than a mark, both
 * spellings are accepted, see sameSpokenWord, which owns all of that. Letters
 * themselves still count: ة and ه are different words, and accepting one for
 * the other teaches the wrong spelling.
 */

import { recitedForm, sameSpokenWord } from './arabicText'
import { shuffled } from './shuffle'
import config from '../memorise.json'
import quiz from '../quiz.json'

/**
 * Every number this file works to, and nothing else. They live in
 * memorise.json, where each one is written out in words beside it, so the
 * rules below can be read as rules instead of as arithmetic. The one
 * exception says on the line above it where it lives and why.
 */
export const PAGE_WORDS = config['page-words']
export const DIFFICULTIES = config.difficulties
export const DEFAULT_DIFFICULTY = config['default-difficulty']
/**
 * How many words a gap offers when the reader is choosing rather than typing.
 * The quiz asks the same question and this is the same answer, so the number
 * is kept once, in quiz.json, and both tabs read it from there.
 */
export const CHOICES = quiz['option-count']
const SPACING_DROPS_AT = config['spacing-drops-at-share']

/** The words of one line, as written. Splitting on spaces is all Arabic needs. */
export const wordsOf = (text) => (text ?? '').split(/\s+/).filter(Boolean)

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

/**
 * Which words of a page are hidden: a set of "lineIndex:wordIndex" keys.
 *
 * @param page   the lines of one page
 * @param share  the fraction of words to hide, 0 to 1
 * @param random a function returning 0..1, from makeRandom
 */
export function blanksFor(page, share, random) {
  const blanks = new Set()
  // From this share up there is no way to keep two gaps apart, so the rule is
  // dropped for everyone above that line rather than for the odd word.
  const spaced = share < SPACING_DROPS_AT

  page.forEach((line, l) => {
    const words = wordsOf(line.arabic)
    // The first word stays. A line of one word therefore offers nothing, which
    // is correct: قُلْ on its own is the cue, not the answer.
    const choosable = words.map((_, w) => w).slice(1)
    const wanted = Math.round(choosable.length * share)
    if (wanted <= 0) return

    // Shuffled, then taken in order, so the gaps land across the whole line
    // instead of clustering wherever the first few draws happened to fall.
    let taken = 0
    for (const w of shuffled(choosable, random)) {
      if (taken >= wanted) break
      if (spaced && (blanks.has(`${l}:${w - 1}`) || blanks.has(`${l}:${w + 1}`))) continue
      blanks.add(`${l}:${w}`)
      taken += 1
    }
  })

  return blanks
}

/**
 * A page said entirely from memory: every word covered but the one to start on.
 *
 * This is a different question from blanksFor, not a harder setting of it. A
 * page with gaps in it is a page you read, stopping at each gap; a page recited
 * from memory has nothing to read at all. So the two rules blanksFor keeps,
 * every line keeping its own first word and no two gaps touching, are both
 * wrong here: they would leave the opening of every ayah on the screen, and
 * somebody reciting a surah is not given the start of each of its ayahs.
 *
 * One word is shown, and only one: the word to begin on, because a reciter
 * needs to know where they are starting and nothing more. Words before it are
 * left as they are printed. They are not part of this attempt, nobody claimed
 * to be reciting them, and covering them would leave rows of blanks that
 * nothing said afterwards can ever uncover.
 *
 * @param page      the lines of one page
 * @param startWord which word of the page, counted across all its lines, to
 *                  begin on
 */
export function fromMemory(page, startWord = 0) {
  const blanks = new Set()
  let at = 0
  page.forEach((line, l) => {
    wordsOf(line.arabic).forEach((_, w) => {
      if (at > startWord) blanks.add(`${l}:${w}`)
      at += 1
    })
  })
  return blanks
}

/**
 * The words a gap offers, one of them right; for the reader who would rather
 * pick than type.
 *
 * The wrong ones are taken from the same part of the book, never from a list
 * written here: a word from elsewhere in the surah is one the reader has just
 * been reading, so it is genuinely tempting, and it stays true to whatever book
 * is loaded rather than to the Qur'an in particular.
 *
 * Tempting is measured, not asserted. A word that opens with the same letters
 * as the answer and runs to about the same length is the one that makes you
 * stop and think; a word of a different length starting elsewhere in the
 * alphabet is dismissed without reading it. Ties are broken at random, so the
 * same gap does not always offer the same three.
 *
 * Fewer than CHOICES come back when the book has nothing else to offer, a
 * short surah, rather than a word being repeated to pad the row out.
 */
export function optionsFor(answer, pool, random, count = CHOICES) {
  const target = recitedForm(answer)
  const already = new Set([target])
  const candidates = []
  for (const word of pool) {
    const form = recitedForm(word)
    if (form === '' || already.has(form)) continue
    already.add(form)
    candidates.push({ word, form })
  }

  const sharedOpening = (form) => {
    let i = 0
    while (i < form.length && i < target.length && form[i] === target[i]) i += 1
    return i
  }

  const options = candidates
    .map((c) => ({
      word: c.word,
      opening: -sharedOpening(c.form),
      length: Math.abs(c.form.length - target.length),
      toss: random(),
    }))
    .sort((a, b) => a.opening - b.opening || a.length - b.length || a.toss - b.toss)
    .slice(0, count - 1)
    .map((c) => c.word)

  options.push(answer)
  return shuffled(options, random)
}

/** True when what was typed is the word that was taken out. */
export const isRight = (typed, actual) => sameSpokenWord(typed, actual)

/** How many gaps were filled correctly, out of how many there were. */
export function score(page, blanks, answers) {
  let right = 0
  for (const key of blanks) {
    const [l, w] = key.split(':').map(Number)
    if (isRight(answers[key] ?? '', wordsOf(page[l].arabic)[w])) right += 1
  }
  return { right, total: blanks.size }
}
