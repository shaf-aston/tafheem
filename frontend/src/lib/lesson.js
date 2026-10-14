/**
 * One Grow lesson: which words, in what order, as which cards. Pure, so no
 * React and no network: the Words world hands in the word table, what has been
 * answered before and what the server says is due, and gets the cards back.
 *
 * Nothing about asking a word is decided here. The question itself is the
 * quiz's own (lib/quiz.js buildQuestion), so a word asked in Grow is the same
 * question, filed under the same module and id, as in the Quiz tab: learn it in
 * one and the other knows.
 *
 * A lesson is mostly review with a few new words:
 *   - `fresh` words never answered before, in the set's own order, each taught
 *     first (a teach card) and then asked;
 *   - the rest are words due for review, longest overdue first;
 *   - too few due and the lesson tops up with more new words, up to `most`, so a
 *     first lesson is neither tiny nor a flood of new words.
 */
import { buildQuestion } from './quiz'

/**
 * The words of one lesson. `order` is the set walked through, in its own order;
 * `all` every word (a word due may sit outside the set); `seen` the ids
 * answered before; `due` the ids due now, longest overdue first; `fresh` how
 * many new words to teach, `most` how many at most when there is little to
 * review, and `size` how many words in all.
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

/**
 * The cards, new and review woven together so a lesson never front-loads all
 * its new words: teach a word, ask it, then a review, then the next new word.
 * `all` is where the wrong options come from.
 */
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

/**
 * The cards after card `at` was answered wrong: it comes back once at the end,
 * so the lesson closes on getting it right. A card already given its second
 * chance is not added again.
 */
export function requeue(cards, at) {
  const card = cards[at]
  if (card.again) return cards
  return [...cards, { ...card, id: `${card.id}:again`, again: true }]
}

/**
 * Where `learnt` words stand among the world's stages (worlds.json): the stage
 * being worked on (0-based), how far into it, and how many it needs. Past the
 * last stage, `done` is true and the last stage reads full.
 */
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
