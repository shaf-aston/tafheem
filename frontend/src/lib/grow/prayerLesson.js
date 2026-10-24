/**
 * Prayer world cards: the words said in and around salah (backend data/grow/worlds/prayer, served by /api/grow/worlds/prayer).
 * An item is a step with `arabic` to say: the dua after wudu, the words of salah, the adhkar after it. Postures and
 * surahs are left to the Fiqh and Quran worlds, which teach them. Per phrase: a teach card (the words, their meaning,
 * and the scholar's line on them, quoted), "what does it mean?", and "complete it" when it has more than one word.
 */
import { bare, gapOf } from '../quiz/gap'
import { weave } from './lesson'
import { shuffled } from '../text/shuffle'

export const MODULE = 'prayer'
export const keyOfPhrase = (phrase) => phrase.id

/** The phrases of a served world, in its paths' order; words said twice (the takbir, again in the 33s) are one phrase. */
export function phrasesOf(world) {
  const said = new Set()
  const phrases = []
  for (const path of world.paths) {
    for (const step of path.steps) {
      const words = bare(step.arabic ?? '').trim()
      if (!words || said.has(words)) continue
      said.add(words)
      phrases.push({ id: step.id, title: step.title, arabic: step.arabic, meaning: step.meaning, ruling: step.ruling ?? null, path: path.title })
    }
  }
  return phrases
}

// The scholar's line under a teach card: who said it, and what, in our English.
const noteOf = (ruling) => (ruling ? `${ruling.known_as}, ${ruling.book}: ${ruling.english}` : undefined)

/** "What does it mean?": the phrase, its meaning among three others. */
function meaningOf(phrase, all, random) {
  const others = shuffled(all.filter((one) => one.id !== phrase.id), random).slice(0, 3)
  const options = shuffled([phrase, ...others], random).map((one) => ({ id: one.id, text: one.meaning }))
  return { prompt: phrase.arabic, options, answerId: phrase.id, answerText: phrase.meaning }
}

const hasGap = (phrase) => phrase.arabic.trim().split(/\s+/).length > 1

/** `picked` from lessonItems; `all` every phrase. A new phrase is asked both ways; a review one way, by chance. */
export function prayerCards(picked, all, random = Math.random) {
  const record = (phrase, ask) => ({ module: MODULE, item: keyOfPhrase(phrase), context: { world: 'prayer', ask } })
  const meaning = (phrase, tag) => {
    const question = meaningOf(phrase, all, random)
    return { kind: 'meaning', id: `ask:${phrase.id}`, tag, ask: 'What does it mean?', question, answerText: question.answerText, record: record(phrase, 'meaning') }
  }
  const gap = (phrase, tag) => {
    const blank = gapOf(phrase.arabic, all.filter((other) => other.id !== phrase.id).map((other) => other.arabic), random)
    return { kind: 'gap', id: `gap:${phrase.id}`, tag, gap: blank, answerText: blank.answer, record: record(phrase, 'gap') }
  }
  return weave(picked, {
    teach: (phrase) => ({ kind: 'teach', id: `teach:${phrase.id}`, tag: phrase.path, ar: phrase.arabic, en: phrase.meaning, note: noteOf(phrase.ruling) }),
    asks: (phrase, isNew) => {
      if (!hasGap(phrase)) return [meaning(phrase, isNew ? 'New phrase' : 'Review')]
      if (isNew) return [meaning(phrase, 'New phrase'), gap(phrase, 'New phrase')]
      return [random() < 0.5 ? meaning(phrase, 'Review') : gap(phrase, 'Review')]
    },
  })
}
