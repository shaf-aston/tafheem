/**
 * A book world's lessons (public/grow/quduri.json): its areas (optional) and parts, each lesson's status from the server
 * summary, and the cards the lesson runner plays. Pure. Status reads a book's index (lib/bookSplit.js: lessons carry
 * `asks`, their question ids) or the whole book alike; cards need the part's own file. A lesson is played whole, teach and
 * ask in the book's order; a review deals only the asking cards that are due. Every Arabic line is the book's.
 */
import { shuffled } from './shuffle'

/** How many due cards one review deals at most. */
export const REVIEW_SIZE = 8

/**
 * The looks a part's path can wear (components/grow/LessonPath.jsx): courtyard stars or a garden of leaves. Parts take
 * them in turn through the book, so neighbours differ and a part is known by sight; a part's own `path` overrides.
 */
export const LOOKS = ['courtyard', 'garden']
const lookAt = (i) => LOOKS[i % LOOKS.length]

const asks = (card) => card.kind !== 'teach'

/** The progress id of a lesson's card: unique across the book. */
export const itemOf = (lesson, card) => `${lesson.id}/${card.id}`

/** The book's lessons, flat, each with its part's id. */
export const lessonsOf = (book) => book.parts.flatMap((part) => part.lessons.map((lesson) => ({ ...lesson, part: part.id })))

/** A lesson's question items: from the index's `asks`, or from its cards. */
const itemsOf = (lesson) => (lesson.asks ?? lesson.cards.filter(asks).map((card) => card.id)).map((id) => `${lesson.id}/${id}`)

/** 'new' (nothing answered), 'started', 'done' (every question answered) or 'learnt' (every one known). */
export function statusOf(lesson, rows) {
  const items = itemsOf(lesson)
  const met = items.filter((item) => rows.has(item))
  if (!met.length) return 'new'
  if (met.length < items.length) return 'started'
  return met.every((item) => rows.get(item).known) ? 'learnt' : 'done'
}

/** An area's or part's lessons finished, of those it has. */
const countOf = (parts) => ({
  finished: parts.reduce((sum, part) => sum + part.finished, 0),
  total: parts.reduce((sum, part) => sum + part.lessons.length, 0),
})

const isOpen = (lesson) => lesson.status === 'new' || lesson.status === 'started'

/**
 * The lesson to take next of `lessons` (with statuses): the first open core one, else the first open `extra` one (a rare
 * case a beginner can leave for later), else null.
 */
export const firstOpen = (lessons) => lessons.find((lesson) => isOpen(lesson) && !lesson.extra) ?? lessons.find(isOpen) ?? null

/**
 * The parts with each lesson's status, how many are finished, the next lesson in the book (firstOpen), what is due, and
 * the areas that group the parts (each with its parts and counts; none when the book has no `areas`).
 */
export function partsOf(book, summary) {
  const rows = new Map(summary.map((row) => [row.item, row]))
  const parts = book.parts.map((part, i) => {
    const lessons = part.lessons.map((lesson) => ({ ...lesson, part: part.id, status: statusOf(lesson, rows) }))
    const finished = lessons.filter((lesson) => lesson.status === 'done' || lesson.status === 'learnt').length
    return { ...part, look: part.path ?? lookAt(i), lessons, finished }
  })
  const next = firstOpen(parts.flatMap((part) => part.lessons))
  const items = new Set(lessonsOf(book).flatMap(itemsOf))
  const due = summary.filter((row) => row.due && items.has(row.item)).sort((a, b) => a.dueAt.localeCompare(b.dueAt)).map((row) => row.item)
  const areas = (book.areas ?? []).map((area, i) => {
    const own = area.parts.map((id) => parts.find((part) => part.id === id)).filter(Boolean)
    return { ...area, look: area.path ?? lookAt(i), parts: own, ...countOf(own) }
  })
  return { parts, areas, next, due }
}

/** The lesson to offer once `lessonId` is finished: the next open one after it in the book, else any still open. */
export function nextAfter(parts, lessonId) {
  const lessons = parts.flatMap((part) => part.lessons)
  const at = lessons.findIndex((lesson) => lesson.id === lessonId)
  const rest = [...lessons.slice(at + 1), ...lessons.slice(0, Math.max(at, 0))]
  return firstOpen(rest)
}

/** The area a part sits in, if the book has areas. */
export const areaOf = (areas, partId) => areas.find((area) => area.parts.some((part) => part.id === partId)) ?? null

/** One authored card as the runner's card. `record` files the answer under the world's `module`, with its id. */
export function cardOf(lesson, card, world, random, tag = lesson.title) {
  const base = { id: itemOf(lesson, card), kind: card.kind, tag, why: card.why }
  const record = { module: world.module, item: itemOf(lesson, card), context: { world: world.id, lesson: lesson.id } }
  switch (card.kind) {
    case 'teach':
      return { ...base, kind: 'rule', title: card.title, ar: card.ar, en: card.en }
    case 'choose': {
      const options = shuffled(card.options.map((text, i) => ({ id: String(i), text })), random)
      return { ...base, ask: card.ask, ar: card.ar, arabic: Boolean(card['arabic-options']), options, answer: String(card.answer), record }
    }
    case 'pick': {
      const options = shuffled(card.options.map((option, i) => ({ id: String(i), text: option.text, right: Boolean(option.right) })), random)
      return { ...base, ask: card.ask, options, record }
    }
    case 'sort':
      return { ...base, ask: card.ask, into: card.into, items: shuffled(card.items.map(([text, into]) => ({ text, into })), random), record }
    case 'order':
      return { ...base, ask: card.ask, steps: card.steps, deck: shuffled(card.steps, random), record }
    default:
      throw new Error(`Unknown card kind: ${card.kind}`)
  }
}

/** A lesson's cards, in its order; null for a lesson the book does not have. */
export function lessonCards(book, lessonId, world, random = Math.random) {
  const lesson = lessonsOf(book).find((one) => one.id === lessonId)
  return lesson ? lesson.cards.map((card) => cardOf(lesson, card, world, random)) : null
}

/** The parts a review of `due` items draws on (the index tells which part each lesson is in), in no set order. */
export function partsDue(book, due) {
  const partOfLesson = new Map(lessonsOf(book).map((lesson) => [lesson.id, lesson.part]))
  return [...new Set(due.slice(0, REVIEW_SIZE).map((item) => partOfLesson.get(item.split('/')[0])).filter(Boolean))]
}

/** The part a lesson is in, from the index. */
export const partOfLesson = (book, lessonId) => lessonsOf(book).find((lesson) => lesson.id === lessonId)?.part ?? null

/** The asking cards whose items are `due` (most overdue first), up to REVIEW_SIZE. `book` holds the parts with cards. */
export function reviewCards(book, due, world, random = Math.random) {
  const byItem = new Map(lessonsOf(book).flatMap((lesson) => lesson.cards.filter(asks).map((card) => [itemOf(lesson, card), [lesson, card]])))
  return due.slice(0, REVIEW_SIZE).filter((item) => byItem.has(item))
    .map((item) => cardOf(...byItem.get(item), world, random, 'Review'))
}
