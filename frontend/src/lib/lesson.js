/**
 * Any lesson world's picking and pacing. Pure. A world's own cards: lib/wordLesson.js, lib/hadithLesson.js, lib/quranLesson.js.
 * A lesson = a few new items (taught, then asked) + items due for review; with little due, more new items up to `most`.
 */

/**
 * The items of one lesson. `order`: the set, in order; `all`: every item; `seen`: ids answered;
 * `due`: ids due, most overdue first; `fresh`/`most`: new items wanted / allowed; `size`: items in all;
 * `keyOf`: an item's progress id.
 */
export function lessonItems({ order, all, seen, due, fresh, most = fresh, size, keyOf }) {
  const byId = new Map(all.map((item) => [keyOf(item), item]))
  const unseen = order.filter((item) => !seen.has(keyOf(item)))
  const taught = unseen.slice(0, Math.min(fresh, size))
  const teaching = new Set(taught.map(keyOf))
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
 * Cards for the picked items, woven: a new item's `teach` card then its `asks`, a review's `asks`,
 * the next new item... `asks(item, isNew)` returns that item's question cards.
 */
export function weave({ fresh, reviews }, { teach, asks }) {
  const cards = []
  for (let i = 0; i < Math.max(fresh.length, reviews.length); i += 1) {
    if (fresh[i]) cards.push(teach(fresh[i]), ...asks(fresh[i], true))
    if (reviews[i]) cards.push(...asks(reviews[i], false))
  }
  return cards
}

/** A wrong card comes back once, at the end. */
export function requeue(cards, at) {
  const card = cards[at]
  if (card.again) return cards
  return [...cards, { ...card, id: `${card.id}:again`, again: true }]
}

/** The current stage (0-based) for `learnt` items, how far into it, and its size; `done` past the last. */
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

/** The set's items with the learner's status: 'known', 'learning' (met, not known yet) or 'new'. `rows`: the server summary. */
export function itemsOf(order, keyOf, rows) {
  const met = new Map(rows.map((row) => [row.item, row.known ? 'known' : 'learning']))
  return order.map((item) => ({ key: keyOf(item), item, status: met.get(keyOf(item)) ?? 'new' }))
}
