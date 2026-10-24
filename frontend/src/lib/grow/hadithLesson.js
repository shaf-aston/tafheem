/**
 * Hadith world cards for an-Nawawi's Forty (public/grow/nawawi40.json, from backend/scripts/build_nawawi40.py).
 * Per hadith: a teach card, "what does it mean?" (key line → English), "complete it" (one word blanked).
 * Every word shown is the source's; key lines are exact quotes (tests/scripts/test_nawawi40.py).
 */
import { gapOf } from '../quiz/gap'
import { weave } from './lesson'
import { shuffled } from '../text/shuffle'
import { moduleOf } from './worlds'

export const MODULE = moduleOf('hadith')
export const SOURCE_URL = '/grow/nawawi40.json'
export const keyOfHadith = (hadith) => String(hadith.n)

/** The gap for a hadith's key line, wrong options from the other key lines. */
const gapFor = (hadith, all, random) =>
  gapOf(hadith.key.ar, all.filter((other) => other.n !== hadith.n).map((other) => other.key.ar), random)

/** "What does it mean?": the Arabic key line, its English among three others. */
function meaningOf(hadith, all, random) {
  const others = shuffled(all.filter((one) => one.n !== hadith.n), random).slice(0, 3)
  const options = shuffled([hadith, ...others], random).map((one) => ({ id: keyOfHadith(one), text: one.key.en }))
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
    const blank = gapFor(hadith, all, random)
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
