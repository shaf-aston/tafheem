/**
 * Grow: one step of a path, said once, and how it went. Pure, so no React, no
 * microphone and no network reach it; the practice card (components/grow/Practice.jsx)
 * is the only caller.
 *
 * Nothing about judging a word is decided here. Lining the words up is
 * follow.js's, weighing the ear's sureness is bySound's, and what each state
 * looks like is reciteColors.js's, so a
 * word marked orange in Grow means exactly what it means in Memorise.
 *
 * What is Grow's own is the honesty of the score:
 *   - a recitation is clean only when every word came back right. "Not sure"
 *     is not right, so it never counts towards anything;
 *   - a step is learnt only once it has been said clean on `clean-days`
 *     different days (grow.json). One good run is a good run, not learnt.
 *     The one exception is a posture, which cannot be heard: the reader's
 *     own Done makes it learnt;
 * */
import config from '../../config/grow.json'
import { sameSpokenWord } from '../text/arabicText'
import { CHECK, MISSED, SAID, WAITING, WRONG, bySound, follow, wordsHeard } from '../recite/follow'
import { wordsOf } from '../memorise/memorise'
import { soundsTheSame } from '../speech/soundalike'
import recite from '../../config/recite.json'

/**
 * A step as one run of words, and where each ayah of it starts in that run,
 * so the ear's scores for an ayah land back on that ayah's words. `ayahText`
 * maps "1:2" to its printed Arabic; a phrase step needs none.
 */
export const pageOf = (step, ayahText) => {
  if (!step.ayahs.length) return { words: wordsOf(step.arabic), ayahs: [] }
  const words = []
  const ayahs = []
  for (const key of step.ayahs) {
    const said = wordsOf(ayahText[key])
    ayahs.push({ key, from: words.length, count: said.length })
    words.push(...said)
  }
  return { words, ayahs }
}

/**
 * One word said for a one-word step. follow.js waits for two words of a page
 * before it marks anything, which is right for a page and means a step of one
 * word, آمين, would never be marked at all.
 */
const oneWord = (printed, heard) => {
  if (!heard.length) return MISSED
  if (heard.some((word) => sameSpokenWord(word, printed))) return SAID
  return heard.some((word) => soundsTheSame(word, printed)) ? CHECK : WRONG
}

/**
 * Every word of the step, marked, once the reader has stopped.
 *
 * `heard` is the transcript, `scores` the ear's score per word of the step
 * (sparse is fine: a word with none is judged on the transcript alone, and
 * bySound never lets that alone make it red). Nothing of the step heard at
 * all marks every word "not said"; the sound can still rescue each of them.
 */
const markRecitation = (words, heard, scores) => {
  const said = wordsHeard(heard)
  let marks
  if (words.length < recite['anchor-words']) {
    marks = { words: words.map((word) => ({ word, state: oneWord(word, said), heard: '' })), extras: [] }
  } else {
    marks = follow(words, said, { startAt: 0, ended: true })
    if (!marks.started) {
      marks = { ...marks, words: words.map((word) => ({ word, state: MISSED, heard: '' })) }
    }
  }
  const marked = bySound(marks, scores)
  return { ...marked, words: marked.words.map((mark) => (mark.state === WAITING ? { ...mark, state: MISSED } : mark)) }
}

/** Whether every word came back right. "Not sure" is not right. */
export const isClean = (marks) => marks.words.length > 0 && marks.words.every((mark) => mark.state === SAID)

/**
 * The whole verdict on one recitation. `scores` is null when the sound could not
 * be checked, and clean also needs the sound weighed for every word: a run the
 * ear could not check is shown and never counted.
 */
export const judge = (words, text, scores) => {
  const weighed = words.length > 0 && scores != null && words.every((_, i) => scores[i] != null)
  const marks = markRecitation(words, text, scores ?? [])
  return { marks, weighed, clean: weighed && isClean(marks) }
}

/** How many words were each state, for the one line said under a recitation. */
export const tally = (marks) => {
  const out = { [SAID]: 0, [CHECK]: 0, [WRONG]: 0, [MISSED]: 0 }
  for (const mark of marks.words) if (mark.state in out) out[mark.state] += 1
  return out
}

/** Today as the reader's own calendar has it, "2026-09-28". */
export const today = (now = new Date()) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/**
 * The record after one recitation of `stepId`. A clean one adds today to the
 * step's clean days (once however many times it is said today); every one
 * counts as a try, which is shown and never scored.
 */
export const afterRecitation = (record, stepId, clean, day = today()) => {
  const was = record[stepId] ?? { tries: 0, cleanDays: [] }
  const cleanDays = clean && !was.cleanDays.includes(day) ? [...was.cleanDays, day] : was.cleanDays
  return { ...record, [stepId]: { tries: was.tries + 1, cleanDays } }
}

/** How many different days a step has been said clean. */
export const daysOf = (record, stepId) => record[stepId]?.cleanDays.length ?? 0

export const isLearnt = (record, stepId) => record[stepId]?.done === true || daysOf(record, stepId) >= config['clean-days']

/**
 * Whether saying this step clean just now is the one that makes it learnt, so
 * the page can celebrate the moment and not every run after it.
 */
export const becomesLearnt = (record, stepId, clean) =>
  !isLearnt(record, stepId) && isLearnt(afterRecitation(record, stepId, clean), stepId)
