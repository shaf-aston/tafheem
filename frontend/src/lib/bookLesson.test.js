import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import book from '../../public/grow/quduri.json'
import { cardOf, lessonCards, lessonsOf, partsOf, reviewCards, statusOf } from './bookLesson'

const BOOK = readFileSync(join(import.meta.dirname, '../../../backend/data/books/openiti', book.file), 'utf8')

// A Kitab's paragraphs as the reader sees them: a `# ` line and its `~~` continuations, page and manuscript marks gone.
function paragraphsOf(kitab) {
  const lines = BOOK.split('\n')
  const start = lines.findIndex((line) => line.startsWith('### | ') && line.endsWith(kitab))
  const paragraphs = []
  for (const line of lines.slice(start + 1)) {
    if (line.startsWith('### | ')) break
    if (line.startsWith('# ')) paragraphs.push(line.slice(2))
    else if (line.startsWith('~~') && paragraphs.length) paragraphs[paragraphs.length - 1] += ` ${line.slice(2)}`
  }
  return paragraphs.map((text) => text.replace(/PageV\d+P\d+|ms\d+/g, ' ').replace(/\s+/g, ' ').trim()).filter(Boolean)
}

// Each card's Arabic: the teach line, the source quotes, a gap line with its answer filled in.
function quotesOf(card) {
  const quotes = [card.ar, ...[card.source ?? []].flat()].filter(Boolean)
  return quotes.map((quote) => (quote.includes('____') ? quote.replace('____', card.options[card.answer]) : quote))
}

// A part's Kitabs: most are one, a few join small ones.
const kitabsOf = (part) => part.kitabs ?? [part.kitab]
const partText = (part) => kitabsOf(part).flatMap(paragraphsOf)

const seq = (...values) => { let i = 0; return () => values[i++ % values.length] }

describe('the Quduri lessons', () => {
  for (const part of book.parts.filter((one) => one.lessons.length)) {
    const text = partText(part).join(' ')

    it(`quotes ${part.title} word for word`, () => {
      expect(text.length).toBeGreaterThan(0)
      const missing = lessonsOf({ parts: [part] }).flatMap((lesson) =>
        lesson.cards.flatMap((card) => quotesOf(card).filter((quote) => !text.includes(quote)).map((quote) => `${lesson.id}/${card.id}: ${quote}`)))
      expect(missing).toEqual([])
    })

    it(`gives every question in ${part.title} a source and a reason`, () => {
      const bare = lessonsOf({ parts: [part] }).flatMap((lesson) => lesson.cards
        .filter((card) => card.kind !== 'teach' && (!card.source || !card.why)).map((card) => `${lesson.id}/${card.id}`))
      expect(bare).toEqual([])
    })

    if (part.whole) {
      it(`covers every paragraph of ${part.title}`, () => {
        const quotes = lessonsOf({ parts: [part] }).flatMap((lesson) => lesson.cards.flatMap(quotesOf))
        let at = 0
        const spans = partText(part).map((paragraph) => {
          const from = text.indexOf(paragraph, at)
          at = from + paragraph.length
          return { paragraph, from, to: at }
        })
        const hits = quotes.map((quote) => { const from = text.indexOf(quote); return { from, to: from + quote.length } })
        const untouched = spans.filter(({ from, to }) => !hits.some((hit) => hit.from < to && hit.to > from)).map(({ paragraph }) => paragraph)
        expect(untouched).toEqual([])
      })
    }
  }

  it('gives every Kitab of the book to exactly one part, and every part to exactly one area', () => {
    const kitabs = BOOK.split('\n').filter((line) => line.startsWith('### | ')).map((line) => line.split(' - ').pop())
    const claimed = book.parts.flatMap(kitabsOf)
    expect([...claimed].sort()).toEqual([...kitabs].sort())
    const placed = book.areas.flatMap((area) => area.parts)
    expect([...placed].sort()).toEqual(book.parts.map((part) => part.id).sort())
  })

  it('has unique lesson ids across the book and unique card ids in a lesson', () => {
    const lessons = lessonsOf(book)
    expect(new Set(lessons.map((lesson) => lesson.id)).size).toBe(lessons.length)
    for (const lesson of lessons) expect(new Set(lesson.cards.map((card) => card.id)).size).toBe(lesson.cards.length)
  })

  it('keeps every answer among its options', () => {
    for (const lesson of lessonsOf(book)) {
      for (const card of lesson.cards) {
        if (card.kind === 'choose') expect(card.options[card.answer]).toBeDefined()
        if (card.kind === 'pick') expect(card.options.some((option) => option.right)).toBe(true)
        if (card.kind === 'sort') for (const [, into] of card.items) expect(card.into).toContain(into)
      }
    }
  })
})

const LESSON = {
  id: 'l1',
  title: 'One',
  cards: [
    { kind: 'teach', id: 't', title: 'T', ar: 'أ', en: 'a' },
    { kind: 'choose', id: 'c', ask: '?', options: ['yes', 'no'], answer: 0, why: 'w' },
    { kind: 'order', id: 'o', ask: '?', steps: ['1', '2', '3'], why: 'w' },
  ],
}
const BOOK_OF = { parts: [{ id: 'p', lessons: [LESSON] }, { id: 'q', lessons: [] }] }
const row = (item, extra = {}) => ({ item, known: false, due: false, dueAt: '2026-01-01', ...extra })

describe('lesson status', () => {
  it('goes new → started → done → learnt as its questions are answered and known', () => {
    expect(statusOf(LESSON, new Map())).toBe('new')
    expect(statusOf(LESSON, new Map([['l1/c', row('l1/c')]]))).toBe('started')
    expect(statusOf(LESSON, new Map([['l1/c', row('l1/c')], ['l1/o', row('l1/o')]]))).toBe('done')
    expect(statusOf(LESSON, new Map([['l1/c', row('l1/c', { known: true })], ['l1/o', row('l1/o', { known: true })]]))).toBe('learnt')
  })

  it('points at the first unfinished lesson, counts finished ones, and lists due items oldest first', () => {
    const fresh = partsOf(BOOK_OF, [])
    expect(fresh.next.id).toBe('l1')
    expect(fresh.parts[0].finished).toBe(0)

    const done = partsOf(BOOK_OF, [row('l1/c', { due: true, dueAt: '2026-02-01' }), row('l1/o', { due: true }), row('other/x', { due: true })])
    expect(done.next).toBe(null)
    expect(done.parts[0].finished).toBe(1)
    expect(done.due).toEqual(['l1/o', 'l1/c'])
  })
})

describe('cards', () => {
  it('plays a lesson in its order, files questions under the module, and keeps teach cards unrecorded', () => {
    const cards = lessonCards(BOOK_OF, 'l1', 'quduri', seq(0))
    expect(cards.map((card) => card.kind)).toEqual(['rule', 'choose', 'order'])
    expect(cards[0].record).toBeUndefined()
    expect(cards[1].record).toMatchObject({ module: 'quduri', item: 'l1/c' })
    expect(cards[1].answer).toBe('0')
    expect(lessonCards(BOOK_OF, 'nope', 'quduri')).toBe(null)
  })

  it('shuffles what is offered but keeps the right order to check against', () => {
    const card = cardOf(LESSON, LESSON.cards[2], 'quduri', seq(0))
    expect(card.steps).toEqual(['1', '2', '3'])
    expect([...card.deck].sort()).toEqual(['1', '2', '3'])
    expect(card.deck).not.toEqual(card.steps)
  })

  it('reviews only due questions, tagged as a review', () => {
    const cards = reviewCards(BOOK_OF, ['l1/o', 'gone/x'], 'quduri', seq(0))
    expect(cards.map((card) => [card.id, card.tag])).toEqual([['l1/o', 'Review']])
  })
})
