// How a book world's lesson reads, Duolingo-style: do more than read, short reads, small sorts, no giveaway answers;
// a long part is cut into `units` (the book's own sections), and lessons marked `extra` (rare cases) are few and lead nothing. The book's words are checked in bookLesson.test.js.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import worlds from '../config/worlds.json'
import { lessonsOf } from './bookLesson'

const PUBLIC = join(import.meta.dirname, '../../public')
const BOOKS = worlds.worlds.filter((world) => world.kind === 'book')
  .map((world) => JSON.parse(readFileSync(join(PUBLIC, world.source), 'utf8')))

// The limits: teach cards in a row, words on a teach card, rows in a sort, and the share of English choose cards whose
// right option is the longest (a learner should not pass by picking the longest).
const MOST_READS = 2
const MOST_WORDS = 60
const MOST_ROWS = 5
const MOST_LONGEST = 0.4
// A part this long is cut into units of at least two lessons; extras are at most this share of the book's lessons.
const UNITS_FROM = 6
const MOST_EXTRA = 0.1
const words = (text) => text.split(/\s+/).filter(Boolean).length

describe.each(BOOKS)('the $book lessons, as lessons', (book) => {
  const lessons = lessonsOf(book)
  const where = (lesson, card) => `${lesson.id}/${card.id}`

  it(`never has more than ${MOST_READS} teach cards in a row`, () => {
    const long = lessons.flatMap((lesson) => {
      let run = 0
      return lesson.cards.flatMap((card) => {
        run = card.kind === 'teach' ? run + 1 : 0
        return run > MOST_READS ? [where(lesson, card)] : []
      })
    })
    expect(long).toEqual([])
  })

  it(`keeps every teach card to ${MOST_WORDS} words of English`, () => {
    const long = lessons.flatMap((lesson) => lesson.cards
      .filter((card) => card.kind === 'teach' && words(card.en) > MOST_WORDS).map((card) => where(lesson, card)))
    expect(long).toEqual([])
  })

  it(`sorts at most ${MOST_ROWS} rows at once`, () => {
    const big = lessons.flatMap((lesson) => lesson.cards
      .filter((card) => card.kind === 'sort' && card.items.length > MOST_ROWS).map((card) => where(lesson, card)))
    expect(big).toEqual([])
  })

  it('does not give the answer away by its length', () => {
    const asked = lessons.flatMap((lesson) => lesson.cards)
      .filter((card) => card.kind === 'choose' && !card['arabic-options'] && card.options.length >= 3)
    const longest = asked.filter((card) => {
      const right = card.options[card.answer].length
      return card.options.every((option, i) => i === card.answer || option.length < right)
    })
    expect(longest.length / asked.length).toBeLessThanOrEqual(MOST_LONGEST)
  })

  it(`cuts every part of ${UNITS_FROM} lessons or more into units, in the lessons' order`, () => {
    for (const part of book.parts.filter((one) => one.units || one.lessons.length >= UNITS_FROM)) {
      expect(part.units?.flatMap((unit) => unit.lessons), part.id).toEqual(part.lessons.map((lesson) => lesson.id))
      for (const unit of part.units) {
        expect(unit.lessons.length, `${part.id}: ${unit.title}`).toBeGreaterThanOrEqual(2)
        expect(unit.title && unit.arabic, `${part.id}: ${unit.title}`).toBeTruthy()
      }
    }
  })

  it('opens every part and unit with a core lesson, and keeps extras to a few', () => {
    for (const part of book.parts.filter((one) => one.lessons.length)) {
      const firsts = [part.lessons[0].id, ...(part.units ?? []).map((unit) => unit.lessons[0])]
      expect(part.lessons.filter((lesson) => lesson.extra && firsts.includes(lesson.id)).map((lesson) => lesson.id), part.id).toEqual([])
    }
    expect(lessons.filter((lesson) => lesson.extra).length).toBeLessThanOrEqual(Math.ceil(lessons.length * MOST_EXTRA))
  })
})
