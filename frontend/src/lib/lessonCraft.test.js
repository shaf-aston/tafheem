// How a book world's lesson reads, Duolingo-style: do more than read, short reads, small sorts, no giveaway answers,
// and lessons marked `extra` (rare cases) never lead a part. The book's words are checked in bookLesson.test.js.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import worlds from '../worlds.json'
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

  it('opens every part with a core lesson, and keeps extras to a few', () => {
    for (const part of book.parts.filter((one) => one.lessons.length)) {
      expect(part.lessons[0].extra, part.id).toBeFalsy()
      expect(part.lessons.filter((lesson) => lesson.extra).length, part.id).toBeLessThanOrEqual(Math.ceil(part.lessons.length / 3))
    }
  })
})
