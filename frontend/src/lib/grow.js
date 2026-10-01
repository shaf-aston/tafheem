/**
 * Grow: one step of a path, said once, and how it went, and where each step
 * stands on the map. Pure, so no React, no microphone and no network reach it;
 * GrowPanel and the map under it are the only callers.
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
 *   - the score counts learnt steps and nothing else. Steps opened, steps
 *     tried, recitations that were nearly right: none of them are counted.
 */
import config from '../grow.json'
import { sameSpokenWord } from './arabicText'
import { CHECK, MISSED, SAID, WAITING, WRONG, bySound, follow, wordsHeard } from './follow'
import { streakAt } from './mascot'
import { wordsOf } from './memorise'
import { moodFrom } from './mood'
import { soundsTheSame } from './soundalike'
import recite from '../recite.json'

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
 * `heard` is the transcript, `sure` the ear's sureness per word of the step
 * (sparse is fine: a word with none is judged on the transcript alone, and
 * bySound never lets that alone make it red). Nothing of the step heard at
 * all marks every word "not said"; the sound can still rescue each of them.
 */
const markRecitation = (words, heard, sure) => {
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
  const marked = bySound(marks, sure)
  return { ...marked, words: marked.words.map((mark) => (mark.state === WAITING ? { ...mark, state: MISSED } : mark)) }
}

/** Whether every word came back right. "Not sure" is not right. */
export const isClean = (marks) => marks.words.length > 0 && marks.words.every((mark) => mark.state === SAID)

/**
 * The whole verdict on one recitation. `sure` is null when the sound could not
 * be checked, and clean also needs the sound weighed for every word: a run the
 * ear could not check is shown and never counted.
 */
export const judge = (words, text, sure) => {
  const weighed = words.length > 0 && sure != null && words.every((_, i) => sure[i] != null)
  const marks = markRecitation(words, text, sure ?? [])
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

/** The record after the reader ticks a posture off: learnt at once, no days to count. */
export const afterDone = (record, stepId) => ({ ...record, [stepId]: { tries: (record[stepId]?.tries ?? 0) + 1, cleanDays: [], done: true } })

/**
 * Where a circle on the map stands, from the one record. `steps` is the single
 * step behind a step's circle, or the several behind a group's, and `open` is
 * whether its tier is open. Four answers, drawn as a lock, a seed, a sprout
 * and a flower:
 *   locked   its tier is not open yet
 *   open     ready, never tried
 *   started  tried or said clean once, not yet learnt
 *   learnt   every step said clean on enough different days
 */
export const nodeState = (steps, record, open = true) => {
  if (!open) return 'locked'
  if (steps.length && steps.every((step) => isLearnt(record, step.id))) return 'learnt'
  const started = (step) => (record[step.id]?.tries ?? 0) > 0 || daysOf(record, step.id) > 0
  return steps.some(started) ? 'started' : 'open'
}

/** The tiers of grow.json, each with the paths that name it. */
export const tiersOf = (tiers, paths = []) =>
  tiers.map((tier) => ({ ...tier, paths: paths.filter((path) => path.tier === tier.id) }))

const stepsOf = (tier) => tier.paths.flatMap((path) => path.steps)

/** Learnt steps over all steps of every path. Only learnt counts. */
export const score = (tiers, record) => {
  const steps = tiers.flatMap(stepsOf)
  return { learnt: steps.filter((step) => isLearnt(record, step.id)).length, total: steps.length }
}

/**
 * Whether tier `i` is open: it has a path, and the tier before it is open and
 * every step of it is learnt. The first tier is open as soon as it has a path.
 * A tier nobody has written yet is never open, however much is learnt before it.
 */
export const unlocked = (tiers, i, record) =>
  tiers[i].paths.length > 0 &&
  (i === 0 || (unlocked(tiers, i - 1, record) && stepsOf(tiers[i - 1]).every((step) => isLearnt(record, step.id))))

/**
 * The nodes of a tier's vine, each a group with its step objects. A tier with
 * paths uses the paths' own groups; one without shows its proposed topics as a
 * single locked group, so the road ahead is visible before it is built.
 */
export const groupsOf = (tier) => {
  if (!tier.paths.length) {
    const steps = tier.proposed.map(({ about, ...one }) => ({ ...one, ayahs: [], meaning: about, proposed: true }))
    return steps.length ? [{ id: `${tier.id}-proposed`, title: 'Steps', arabic: '', icon: 'lock', steps }] : []
  }
  return tier.paths.flatMap((path) => path.groups.map((group) => ({
    ...group,
    path: path.id,
    steps: group.steps.map((id) => path.steps.find((step) => step.id === id)),
  })))
}

/**
 * Everything the map draws, in one pass: each tier with whether it is open and
 * how much of it is learnt, its paths, and each path's groups with every step's
 * state. A group marked `alongside` runs through its whole path rather than
 * after the group before it, so it is kept apart for the map to draw beside.
 */
export const mapOf = (tiers, record, next) => tiers.map((tier, i) => {
  const open = unlocked(tiers, i, record)
  const groups = groupsOf(tier).map((group) => {
    const steps = group.steps.map((step) => ({ step, state: nodeState([step], record, open), now: step === next }))
    return { group, steps, state: nodeState(group.steps, record, open), learnt: steps.filter((one) => one.state === 'learnt').length }
  })
  const paths = (tier.paths.length ? tier.paths : [{ id: tier.id, title: '', arabic: '' }]).map((path) => {
    const own = groups.filter((one) => (one.group.path ?? tier.id) === path.id)
    return { path, groups: own.filter((one) => !one.group.alongside), alongside: own.filter((one) => one.group.alongside) }
  })
  const learnt = groups.reduce((sum, one) => sum + one.learnt, 0)
  const total = groups.reduce((sum, one) => sum + one.steps.length, 0)
  return { tier, i, open, paths, learnt, total }
})

/**
 * Whether saying this step clean just now is the one that makes it learnt, so
 * the page can celebrate the moment and not every run after it.
 */
export const becomesLearnt = (record, stepId, clean) =>
  !isLearnt(record, stepId) && isLearnt(afterRecitation(record, stepId, clean), stepId)

/**
 * Qalam's reaction to a recitation: a right one is a nod, a wrong one a
 * droop, and a run of right ones in this visit is the hop. `streak` counts
 * right ones in a row, this one included.
 */
export const reactionTo = (clean, streak) => moodFrom(clean && streak >= streakAt ? { streak } : { answer: clean ? 'correct' : 'wrong' })

/** The step to work on next: the first not yet learnt in an open tier, else none. */
export const upNext = (tiers, record) => {
  for (let i = 0; i < tiers.length; i += 1) {
    if (!unlocked(tiers, i, record)) return null
    const step = stepsOf(tiers[i]).find((one) => !isLearnt(record, one.id))
    if (step) return step
  }
  return null
}
