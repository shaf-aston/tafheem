// Every book world's glossary: each term has its Arabic, a short plain English line, and the lesson that first teaches it; no term twice.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import worlds from '../worlds.json'
import { lessonsOf } from './bookLesson'

const PUBLIC = join(import.meta.dirname, '../../public')
const BOOKS = worlds.worlds.filter((world) => world.kind === 'book')
  .map((world) => JSON.parse(readFileSync(join(PUBLIC, world.source), 'utf8')))
const MOST_WORDS = 25
const words = (text) => text.split(/\s+/).filter(Boolean).length

describe.each(BOOKS)('the $book glossary', (book) => {
  const ids = new Set(lessonsOf(book).map((lesson) => lesson.id))

  it('has terms', () => {
    expect(book.glossary?.length).toBeGreaterThan(0)
  })

  it(`gives every term its Arabic, ${MOST_WORDS} words of English at most, and a lesson in the book`, () => {
    const bad = book.glossary
      .filter((entry) => !entry.term || !entry.ar || !entry.en || words(entry.en) > MOST_WORDS || !ids.has(entry.lesson))
      .map((entry) => entry.term)
    expect(bad).toEqual([])
  })

  it('lists each term once', () => {
    const terms = book.glossary.map((entry) => entry.term)
    expect(terms.filter((term, i) => terms.indexOf(term) !== i)).toEqual([])
  })
})
