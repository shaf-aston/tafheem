/**
 * A book world's lessons (public/grow/quduri.json): its areas (optional) and parts, each lesson's status from the server summary, and the cards
 * the lesson runner plays. Pure. A lesson is played whole, teach and ask in the book's order; a review deals only the
 * asking cards that are due. Every Arabic line is the book's (lib/bookLesson.test.js).
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

/** 'new' (nothing answered), 'started', 'done' (every question answered) or 'learnt' (every one known). */
export function statusOf(lesson, rows) {
  const items = lesson.cards.filter(asks).map((card) => itemOf(lesson, card))
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

/**
 * The parts with each lesson's status, how many are finished, the first unfinished lesson in the book, what is due, and
 * the areas that group the parts (each with its parts and counts; none when the book has no `areas`).
 */
export function partsOf(book, summary) {
  const rows = new Map(summary.map((row) => [row.item, row]))
  const parts = book.parts.map((part, i) => {
    const lessons = part.lessons.map((lesson) => ({ ...lesson, part: part.id, status: statusOf(lesson, rows) }))
    const finished = lessons.filter((lesson) => lesson.status === 'done' || lesson.status === 'learnt').length
    return { ...part, look: part.path ?? lookAt(i), lessons, finished }
  })
  const next = parts.flatMap((part) => part.lessons).find((lesson) => lesson.status === 'new' || lesson.status === 'started') ?? null
  const items = new Set(lessonsOf(book).flatMap((lesson) => lesson.cards.filter(asks).map((card) => itemOf(lesson, card))))
  const due = summary.filter((row) => row.due && items.has(row.item)).sort((a, b) => a.dueAt.localeCompare(b.dueAt)).map((row) => row.item)
  const areas = (book.areas ?? []).map((area, i) => {
    const own = area.parts.map((id) => parts.find((part) => part.id === id)).filter(Boolean)
    return { ...area, look: area.path ?? lookAt(i), parts: own, ...countOf(own) }
  })
  return { parts, areas, next, due }
}

/** The area a part sits in, if the book has areas. */
export const areaOf = (areas, partId) => areas.find((area) => area.parts.some((part) => part.id === partId)) ?? null

/** One authored card as the runner's card. `record` files the answer under `module`. */
export function cardOf(lesson, card, module, random, tag = lesson.title) {
  const base = { id: itemOf(lesson, card), kind: card.kind, tag, why: card.why }
  const record = { module, item: itemOf(lesson, card), context: { world: 'fiqh', lesson: lesson.id } }
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
export function lessonCards(book, lessonId, module, random = Math.random) {
  const lesson = lessonsOf(book).find((one) => one.id === lessonId)
  return lesson ? lesson.cards.map((card) => cardOf(lesson, card, module, random)) : null
}

/** The asking cards whose items are `due` (most overdue first), up to REVIEW_SIZE. */
export function reviewCards(book, due, module, random = Math.random) {
  const byItem = new Map(lessonsOf(book).flatMap((lesson) => lesson.cards.filter(asks).map((card) => [itemOf(lesson, card), [lesson, card]])))
  return due.slice(0, REVIEW_SIZE).filter((item) => byItem.has(item))
    .map((item) => cardOf(...byItem.get(item), module, random, 'Review'))
}
