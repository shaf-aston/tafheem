/**
 * The Tamreen exercises: turning the library into one queue to drill, and
 * grading a reader's picks against the teacher's answer.
 *
 * A "rule" question is a tick-every-true-option statement. An "example" is a
 * picture question: a sentence with words underlined in the picture (blue for
 * a possible حال, green for a possible ذو الحال, see markedWords below), and one
 * or more parts. A part is ticked (a grid of rows by options, or a plain list
 * of options) or written (an explanation or a translation). An example may
 * hold any number of each, in any order, and every ticked part must be right
 * for the example to count as right.
 *
 * Pure functions throughout: exercise data and a reader's picks in, a grading
 * shape out. No React, no fetching, no randomness.
 */
import settings from '../tamreen.json'

/** Every setting the practise panel reads, the way quizBanks maps quiz.json. */
export const TAMREEN = {
  autoNext: settings['auto-next'],
  autoNextMs: settings['auto-next-ms'],
  autoNextWrongMs: settings['auto-next-wrong-ms'],
}

/** Every rule and example across every exercise, one flat queue to drill. */
export function buildQueue(exercises) {
  const queue = []
  for (const exercise of exercises ?? []) {
    for (const rule of exercise.rules ?? []) {
      queue.push({ kind: 'rule', item: rule, exerciseKey: exercise.key })
    }
    for (const example of exercise.examples ?? []) {
      queue.push({ kind: 'example', item: example, exerciseKey: exercise.key })
    }
  }
  return queue
}

/** The Arabic line and the English line(s) under it, an example's `sentence` split apart. */
export function sentenceLines(example) {
  const [arabic, ...rest] = (example.sentence ?? '').split('\n')
  return { arabic: arabic ?? '', gloss: rest.join(' ').trim() }
}

const wordsOf = (text) => text.split(/\s+/).filter(Boolean)

/**
 * Which words of the sentence are marked blue (possible حال) and which are
 * marked green (possible ذو الحال), from the picture's `marked` list. Blue
 * wins where a word is named in both, matching the prototype: a حال is the
 * more specific claim about a word than "somewhere in the sentence about it".
 */
export function markedWords(example) {
  const blue = new Set()
  const green = new Set()
  for (const mark of example.marked ?? []) {
    const bucket = mark.style?.startsWith('blue') ? blue : mark.style?.startsWith('green') ? green : null
    if (!bucket) continue
    for (const word of wordsOf(mark.text)) bucket.add(word)
  }
  for (const word of green) if (blue.has(word)) green.delete(word)
  return { blue, green }
}

/** The parts a reader answers by ticking: a grid (rows x options) or a plain list of options. */
export const answerParts = (example) => (example.parts ?? []).filter((p) => p.options)

/** The parts answered in prose (an explanation, a translation), in the order asked. */
export const proseParts = (example) => (example.parts ?? []).filter((p) => !p.options && p.answer)

/** What a placeholder ("A", "?3") points at in the picture, or '' when nothing is recorded. */
export const labelOf = (part, key) => part.labels?.[key] ?? ''

/**
 * A grid row's name as shown: its label, else the row itself, else nothing
 * for a row the form named with bare punctuation ("?", ">"), which only ever
 * meant "this sentence".
 */
export const rowName = (part, row) => labelOf(part, row) || (/[\p{L}\d]/u.test(row) ? row : '')

/**
 * One part's picks out of an example's saved picks, which are kept per part
 * letter. Examples saved before parts were told apart hold the grid's rows
 * directly, and no key of theirs is a part letter.
 */
export function partPicks(picks, part) {
  const own = picks?.[part.letter]
  if (own !== undefined) return own
  const legacy = part.rows && picks && !Object.keys(picks).some((key) => /^[a-z]$/.test(key))
  return legacy ? picks : part.rows ? {} : []
}

/** Every doubt attached to an example: the example's own, and each part's. */
export const doubtsOf = (example) =>
  [example.doubt, ...(example.parts ?? []).map((p) => p.doubt)].filter(Boolean)

/**
 * Grade a rule question: `picked` is the set of option strings ticked.
 * Each option comes back with its own status, so the UI can colour it without
 * re-deriving the logic: 'ok' (ticked and right), 'bad' (ticked and wrong),
 * 'miss' (right but not ticked), '' (wrong and rightly left alone).
 */
export function gradeRule(rule, picked) {
  const answer = new Set(rule.answer)
  const options = rule.options.map((option) => {
    const isPicked = picked.has(option)
    const isRight = answer.has(option)
    const status = isPicked && isRight ? 'ok' : isPicked ? 'bad' : isRight ? 'miss' : ''
    return { option, picked: isPicked, status }
  })
  const correct = options.every((o) => o.status !== 'bad' && o.status !== 'miss')
  return { options, correct }
}

/**
 * Grade one grid part: `picks` is { row: [options...] }. Comes back as one
 * row of graded options per row, same status scheme as gradeRule.
 */
export function gradeGrid(part, picks) {
  const rows = part.rows.map((row) => {
    const answer = new Set(part.answer[row] ?? [])
    const chosen = new Set(picks[row] ?? [])
    const options = part.options.map((option) => {
      const isPicked = chosen.has(option)
      const isRight = answer.has(option)
      const status = isPicked && isRight ? 'ok' : isPicked ? 'bad' : isRight ? 'miss' : ''
      return { option, picked: isPicked, status }
    })
    return { row, options, correct: options.every((o) => o.status !== 'bad' && o.status !== 'miss') }
  })
  return { rows, correct: rows.every((r) => r.correct) }
}

/** Grade one ticking part of an example, grid or list, from the example's saved picks. */
export function gradePart(part, picks) {
  const own = partPicks(picks, part)
  return part.rows ? gradeGrid(part, own) : gradeRule(part, new Set(own))
}

/** True once a queue item has been checked and every part of it came out right. */
export function isFullyCorrect(entry, picks) {
  if (entry.kind === 'rule') return gradeRule(entry.item, new Set(picks ?? [])).correct
  return answerParts(entry.item).every((part) => gradePart(part, picks).correct)
}

/**
 * Where one question stands: 'right' or 'wrong' once checked, '' before.
 * `answers` is { id: { picks, checked } }, the saved state of the whole drill.
 */
export function statusOf(entry, answers) {
  const saved = answers[entry.item.id]
  if (!saved?.checked) return ''
  return isFullyCorrect(entry, saved.picks) ? 'right' : 'wrong'
}

/** The views a reader can narrow the drill to, in the order they are offered. */
export const SHOWS = ['all', 'wrong', 'todo']

/** Question types: 'rule' ticks what a grammar point allows, 'example' parses a sentence (tarkeeb). */
export const KINDS = ['all', 'rule', 'example']

/**
 * Narrow the queue to one topic ('' for every topic) and one view: every
 * question, only the ones got wrong, or only the ones not yet checked.
 */
export function narrowQueue(queue, answers, { tag = '', show = 'all', kind = 'all' } = {}) {
  return queue.filter((entry) => {
    if (tag && !entry.item.tags?.includes(tag)) return false
    if (kind !== 'all' && entry.kind !== kind) return false
    const status = statusOf(entry, answers)
    if (show === 'wrong') return status === 'wrong'
    if (show === 'todo') return status === ''
    return true
  })
}

/** Right, wrong and checked counts over a list of questions. */
export function scoreOf(queue, answers) {
  const score = { right: 0, wrong: 0, total: queue.length }
  for (const entry of queue) {
    const status = statusOf(entry, answers)
    if (status) score[status]++
  }
  return score
}
