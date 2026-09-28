/**
 * Grow: one step of a path, said once, and how it went. Pure, so no React, no
 * microphone and no network reach it; GrowPanel is the only caller.
 *
 * Nothing about judging a word is decided here. Lining the words up is
 * follow.js's, weighing the ear's sureness is bySound's at the reader's own
 * checking level, and what each state looks like is reciteColors.js's, so a
 * word marked orange in Grow means exactly what it means in Memorise.
 *
 * What is Grow's own is the honesty of the score:
 *   - a recitation is clean only when every word came back right. "Not sure"
 *     is not right, so it never counts towards anything;
 *   - a step is mastered only once it has been said clean on `clean-days`
 *     different days (grow.json). One good run is a good run, not mastery;
 *   - the score counts mastered steps and nothing else. Steps opened, steps
 *     tried, recitations that were nearly right: none of them are counted.
 */
import config from '../grow.json'
import { sameSpokenWord } from './arabicText'
import { CHECK, MISSED, SAID, WAITING, WRONG, bySound, follow, wordsHeard } from './follow'
import { wordsOf } from './memorise'
import { soundsTheSame } from './soundalike'
import recite from '../recite.json'

export { wordsOf }

/**
 * A step as one run of words, and where each ayah of it starts in that run,
 * so the ear's scores for an ayah land back on that ayah's words. `ayahText`
 * maps "1:2" to its printed Arabic; a phrase step needs none.
 */
export const pageOf = (step, ayahText = {}) => {
  if (!step?.ayahs?.length) return { words: wordsOf(step?.arabic), ayahs: [] }
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
 * `heard` is the transcript, `sure` the ear's sureness per word of the step
 * (sparse is fine: a word with none is judged on the transcript alone, and
 * bySound never lets that alone make it red). Nothing of the step heard at
 * all marks every word "not said"; the sound can still rescue each of them.
 */
export const markRecitation = (words, heard, sure = [], level = 'standard') => {
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
  const marked = bySound(marks, sure, level)
  return { ...marked, words: marked.words.map((mark) => (mark.state === WAITING ? { ...mark, state: MISSED } : mark)) }
}

/** Whether every word came back right. "Not sure" is not right. */
export const isClean = (marks) =>
  Boolean(marks?.words?.length) && marks.words.every((mark) => mark.state === SAID)

/** How many words were each state, for the one line said under a recitation. */
export const tally = (marks) => {
  const out = { [SAID]: 0, [CHECK]: 0, [WRONG]: 0, [MISSED]: 0 }
  for (const mark of marks?.words ?? []) if (mark.state in out) out[mark.state] += 1
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

export const isMastered = (record, stepId) =>
  (record[stepId]?.cleanDays?.length ?? 0) >= config['clean-days']

/** Mastered steps of a path over all its steps. Only mastered counts. */
export const score = (path, record) => {
  const steps = path?.steps ?? []
  return { mastered: steps.filter((step) => isMastered(record, step.id)).length, total: steps.length }
}

/** The step to open on: the first one not yet mastered, else the first. */
export const nextStep = (path, record) =>
  (path?.steps ?? []).find((step) => !isMastered(record, step.id)) ?? path?.steps?.[0] ?? null

/** Only what a record should hold; anything else in storage is dropped. */
const tidy = (raw) => {
  const out = {}
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return out
  for (const [id, entry] of Object.entries(raw)) {
    const tries = Number.isInteger(entry?.tries) && entry.tries >= 0 ? entry.tries : 0
    const cleanDays = Array.isArray(entry?.cleanDays)
      ? [...new Set(entry.cleanDays.filter((day) => /^\d{4}-\d{2}-\d{2}$/.test(day)))]
      : []
    out[id] = { tries, cleanDays }
  }
  return out
}

/**
 * The reader's record, kept in this browser only. Storage that is missing,
 * blocked or holding something unreadable is an empty record, never an error:
 * nobody should lose the page because a private window forgot their progress.
 */
export const loadRecord = (storage = globalThis.localStorage) => {
  try {
    return tidy(JSON.parse(storage?.getItem(config['storage-key']) ?? '{}'))
  } catch {
    return {}
  }
}

export const saveRecord = (record, storage = globalThis.localStorage) => {
  try {
    storage?.setItem(config['storage-key'], JSON.stringify(record))
  } catch {
    // Full or blocked: the page carries on with what it has in memory.
  }
}
