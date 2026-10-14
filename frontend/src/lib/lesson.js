/**
 * One Grow lesson: which words, as which cards. Pure.
 * Questions are the quiz's own (buildQuestion), filed under the quiz's module, so Grow and Quiz share progress.
 * A lesson = a few new words (taught, then asked) + words due for review; with little due, more new words up to `most`.
 */
import { buildQuestion } from './quiz'

/**
 * The words of one lesson. `order`: the set, in order; `all`: every word; `seen`: ids answered;
 * `due`: ids due, most overdue first; `fresh`/`most`: new words wanted / allowed; `size`: words in all.
 */
export function lessonWords({ order, all, seen, due, fresh, most = fresh, size }) {
  const byId = new Map(all.map((word) => [word.meaningKey, word]))
  const unseen = order.filter((word) => !seen.has(word.meaningKey))
  const taught = unseen.slice(0, Math.min(fresh, size))
  const teaching = new Set(taught.map((word) => word.meaningKey))
  const reviews = due
    .filter((id) => !teaching.has(id))
    .map((id) => byId.get(id))
    .filter(Boolean)
    .slice(0, size - taught.length)
  const room = Math.min(size - taught.length - reviews.length, most - taught.length)
  const more = unseen.slice(taught.length, taught.length + Math.max(0, room))
  return { fresh: [...taught, ...more], reviews }
}

/** The cards, woven: teach a word, ask it, a review, the next word. `all` supplies wrong options. */
export function cardsOf({ fresh, reviews }, all, random = Math.random) {
  const ask = (word, isNew) => ({
    kind: 'meaning',
    id: `ask:${word.meaningKey}`,
    word,
    isNew,
    question: buildQuestion([word], { distractorBank: all, random }),
  })
  const cards = []
  const longest = Math.max(fresh.length, reviews.length)
  for (let i = 0; i < longest; i += 1) {
    if (fresh[i]) cards.push({ kind: 'teach', id: `teach:${fresh[i].meaningKey}`, word: fresh[i] }, ask(fresh[i], true))
    if (reviews[i]) cards.push(ask(reviews[i], false))
  }
  return cards
}

/** A wrong card comes back once, at the end. */
export function requeue(cards, at) {
  const card = cards[at]
  if (card.again) return cards
  return [...cards, { ...card, id: `${card.id}:again`, again: true }]
}

/** The current stage (0-based) for `learnt` words, how far into it, and its size; `done` past the last. */
export function stageOf(learnt, stages) {
  let from = 0
  for (let i = 0; i < stages.length; i += 1) {
    if (learnt < stages[i]) return { stage: i, into: learnt - from, need: stages[i] - from, done: false }
    from = stages[i]
  }
  const last = stages.length - 1
  const start = last > 0 ? stages[last - 1] : 0
  return { stage: last, into: stages[last] - start, need: stages[last] - start, done: true }
}
