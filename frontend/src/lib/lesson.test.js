import { describe, expect, it } from 'vitest'

import { cardsOf, lessonWords, requeue, stageOf } from './lesson'
import { makeRandom } from './quiz'

const word = (id, en = id) => ({ meaningKey: id, ar: `ar-${id}`, en, wordType: 'noun' })
const ORDER = ['a', 'b', 'c', 'd', 'e', 'f'].map((id) => word(id))
const OUTSIDE = word('z')
const ALL = [...ORDER, OUTSIDE, ...['p', 'q', 'r', 's'].map((id) => word(id))]

describe('lessonWords', () => {
  it('teaches the first unseen words in the set order, then reviews what is due', () => {
    const got = lessonWords({ order: ORDER, all: ALL, seen: new Set(['a', 'z']), due: ['z', 'a'], fresh: 2, size: 4 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['b', 'c'])
    expect(got.reviews.map((w) => w.meaningKey)).toEqual(['z', 'a'])
  })

  it('tops up with more new words when too little is due, but no more than most', () => {
    const got = lessonWords({ order: ORDER, all: ALL, seen: new Set(), due: [], fresh: 2, most: 3, size: 5 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['a', 'b', 'c'])
    expect(got.reviews).toEqual([])
  })

  it('tops up to the size when most allows it', () => {
    const got = lessonWords({ order: ORDER, all: ALL, seen: new Set(), due: [], fresh: 2, most: 9, size: 4 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['a', 'b', 'c', 'd'])
  })

  it('caps reviews so the lesson keeps its size', () => {
    const got = lessonWords({ order: ORDER, all: ALL, seen: new Set(['a', 'b', 'c']), due: ['a', 'b', 'c'], fresh: 1, size: 3 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['d'])
    expect(got.reviews.map((w) => w.meaningKey)).toEqual(['a', 'b'])
  })

  it('drops a due id the table no longer has', () => {
    const got = lessonWords({ order: ORDER, all: ALL, seen: new Set(ORDER.map((w) => w.meaningKey)), due: ['gone', 'a'], fresh: 3, size: 3 })
    expect(got.reviews.map((w) => w.meaningKey)).toEqual(['a'])
    expect(got.fresh).toEqual([])
  })
})

describe('cardsOf', () => {
  it('teaches each new word just before asking it, with reviews woven between', () => {
    const cards = cardsOf({ fresh: [ORDER[0], ORDER[1]], reviews: [OUTSIDE] }, ALL, makeRandom(3))
    expect(cards.map((card) => card.id)).toEqual(['teach:a', 'ask:a', 'ask:z', 'teach:b', 'ask:b'])
  })

  it('asks the word with the quiz’s own question', () => {
    const [, ask] = cardsOf({ fresh: [ORDER[0]], reviews: [] }, ALL, makeRandom(3))
    expect(ask.question.answerId).toBe('a')
    expect(ask.question.options.some((option) => option.id === 'a')).toBe(true)
    expect(ask.question.options.length).toBeGreaterThan(1)
  })
})

describe('requeue', () => {
  it('brings a wrong card back once, at the end', () => {
    const cards = [{ id: 'ask:a' }, { id: 'ask:b' }]
    const once = requeue(cards, 0)
    expect(once.map((card) => card.id)).toEqual(['ask:a', 'ask:b', 'ask:a:again'])
    expect(requeue(once, 2)).toBe(once)
  })
})

describe('stageOf', () => {
  const STAGES = [20, 50, 100]
  it('says which stage is being worked on and how far into it', () => {
    expect(stageOf(0, STAGES)).toEqual({ stage: 0, into: 0, need: 20, done: false })
    expect(stageOf(35, STAGES)).toEqual({ stage: 1, into: 15, need: 30, done: false })
  })
  it('reads full past the last stage', () => {
    expect(stageOf(500, STAGES)).toEqual({ stage: 2, into: 50, need: 50, done: true })
  })
})
