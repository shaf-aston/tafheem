/**
 * "Complete it" for any Arabic line: its longest word blanked, three wrong words from other lines.
 * Pure. Used by lib/grow/hadithLesson.js and lib/grow/quranLesson.js; drawn by components/grow/exercises/GapCard.jsx.
 */
import { shuffled } from '../text/shuffle'

const MARKS = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g // signs, harakat, dagger alif, Quranic marks, tatweel
const PUNCT = /[،؛؟!.:]+$/
const END = /[\s۝٠-٩۰-۹]+$/ // an ayah's end mark and number

/** A word with its marks and trailing punctuation gone, for comparing words. */
export const bare = (word) => word.replace(PUNCT, '').replace(MARKS, '')

const wordsOf = (text) => text.replace(END, '').split(/\s+/).filter(Boolean)

/**
 * The gap in `text`; wrong options are words of `otherTexts`, nearest in length.
 * `{ words, at, tail, options, answer }` (tail: punctuation after the blank).
 */
export function gapOf(text, otherTexts, random = Math.random) {
  const words = wordsOf(text)
  let at = 0
  words.forEach((word, i) => { if (bare(word).length > bare(words[at]).length) at = i })
  const answer = words[at].replace(PUNCT, '')
  const target = bare(answer)
  const pool = new Map()
  for (const other of otherTexts) {
    for (const word of wordsOf(other)) {
      const option = word.replace(PUNCT, '')
      const plain = bare(option)
      if (plain !== target && plain.length > 1 && !pool.has(plain)) pool.set(plain, option)
    }
  }
  const nearest = [...pool.values()]
    .sort((a, b) => Math.abs(bare(a).length - target.length) - Math.abs(bare(b).length - target.length))
    .slice(0, 12)
  const options = shuffled([answer, ...shuffled(nearest, random).slice(0, 3)], random).map((option) => ({ id: option, text: option }))
  return { words, at, tail: words[at].slice(answer.length), options, answer }
}
