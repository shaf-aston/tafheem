/**
 * Hadith world cards for an-Nawawi's Forty (public/grow/nawawi40.json, from backend/scripts/build_nawawi40.py).
 * Per hadith: a teach card, "what does it mean?" (key line → English), "complete it" (one word blanked).
 * Every word shown is the source's; key lines are exact quotes (tests/test_nawawi40.py).
 */
import { weave } from './lesson'

export const MODULE = 'nawawi40'
export const SOURCE_URL = '/grow/nawawi40.json'
export const keyOfHadith = (hadith) => String(hadith.n)

const MARKS = /[ً-ْٰـ]/g // harakat, dagger alif, tatweel
const PUNCT = /[،؛؟!.:]+$/
/** A word with its marks and trailing punctuation gone, for comparing words. */
export const bare = (word) => word.replace(PUNCT, '').replace(MARKS, '')

function shuffle(list, random) {
  const out = [...list]
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

/**
 * The gap for a hadith's key line: its longest word blanked; wrong options are words from the other
 * key lines, nearest in length. `{ words, at, tail, options, answer }` (tail: punctuation after the blank).
 */
export function gapOf(hadith, all, random = Math.random) {
  const words = hadith.key.ar.split(' ')
  let at = 0
  words.forEach((word, i) => { if (bare(word).length > bare(words[at]).length) at = i })
  const answer = words[at].replace(PUNCT, '')
  const target = bare(answer)
  const pool = new Map()
  for (const other of all) {
    if (other.n === hadith.n) continue
    for (const word of other.key.ar.split(' ')) {
      const text = word.replace(PUNCT, '')
      const plain = bare(text)
      if (plain !== target && plain.length > 1 && !pool.has(plain)) pool.set(plain, text)
    }
  }
  const nearest = [...pool.values()]
    .sort((a, b) => Math.abs(bare(a).length - target.length) - Math.abs(bare(b).length - target.length))
    .slice(0, 12)
  const options = shuffle([answer, ...shuffle(nearest, random).slice(0, 3)], random).map((text) => ({ id: text, text }))
  return { words, at, tail: words[at].slice(answer.length), options, answer }
}

/** "What does it mean?": the Arabic key line, its English among three others. */
function meaningOf(hadith, all, random) {
  const others = shuffle(all.filter((one) => one.n !== hadith.n), random).slice(0, 3)
  const options = shuffle([hadith, ...others], random).map((one) => ({ id: keyOfHadith(one), text: one.key.en }))
  return { prompt: hadith.key.ar, options, answerId: keyOfHadith(hadith), answerText: hadith.key.en }
}

/** `picked` from lessonItems; `all` the 42. A new hadith is asked both ways; a review one way, by chance. */
export function hadithCards(picked, all, random = Math.random) {
  const record = (hadith, ask) => ({ module: MODULE, item: keyOfHadith(hadith), context: { world: 'hadith', ask } })
  const meaning = (hadith, tag) => {
    const question = meaningOf(hadith, all, random)
    return { kind: 'meaning', id: `ask:${hadith.n}`, tag, ask: 'What does it mean?', question, answerText: question.answerText, record: record(hadith, 'meaning') }
  }
  const gap = (hadith, tag) => {
    const blank = gapOf(hadith, all, random)
    return { kind: 'gap', id: `gap:${hadith.n}`, tag, gap: blank, answerText: blank.answer, record: record(hadith, 'gap') }
  }
  return weave(picked, {
    teach: (hadith) => ({ kind: 'hadith', id: `teach:${hadith.n}`, tag: 'New hadith', hadith }),
    asks: (hadith, isNew) => {
      if (isNew) return [meaning(hadith, 'New hadith'), gap(hadith, 'New hadith')]
      return [random() < 0.5 ? meaning(hadith, 'Review') : gap(hadith, 'Review')]
    },
  })
}
