import { describe, expect, it } from 'vitest'

import { itemsOf, lessonItems, requeue, stageOf, weave } from './lesson'

const word = (id, en = id) => ({ meaningKey: id, ar: `ar-${id}`, en, wordType: 'noun' })
const ORDER = ['a', 'b', 'c', 'd', 'e', 'f'].map((id) => word(id))
const OUTSIDE = word('z')
const ALL = [...ORDER, OUTSIDE, ...['p', 'q', 'r', 's'].map((id) => word(id))]

describe('lessonItems', () => {
  it('teaches the first unseen words in the set order, then reviews what is due', () => {
    const got = lessonItems({ keyOf: (w) => w.meaningKey, order: ORDER, all: ALL, seen: new Set(['a', 'z']), due: ['z', 'a'], fresh: 2, size: 4 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['b', 'c'])
    expect(got.reviews.map((w) => w.meaningKey)).toEqual(['z', 'a'])
  })

  it('tops up with more new words when too little is due, but no more than most', () => {
    const got = lessonItems({ keyOf: (w) => w.meaningKey, order: ORDER, all: ALL, seen: new Set(), due: [], fresh: 2, most: 3, size: 5 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['a', 'b', 'c'])
    expect(got.reviews).toEqual([])
  })

  it('tops up to the size when most allows it', () => {
    const got = lessonItems({ keyOf: (w) => w.meaningKey, order: ORDER, all: ALL, seen: new Set(), due: [], fresh: 2, most: 9, size: 4 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['a', 'b', 'c', 'd'])
  })

  it('caps reviews so the lesson keeps its size', () => {
    const got = lessonItems({ keyOf: (w) => w.meaningKey, order: ORDER, all: ALL, seen: new Set(['a', 'b', 'c']), due: ['a', 'b', 'c'], fresh: 1, size: 3 })
    expect(got.fresh.map((w) => w.meaningKey)).toEqual(['d'])
    expect(got.reviews.map((w) => w.meaningKey)).toEqual(['a', 'b'])
  })

  it('drops a due id the table no longer has', () => {
    const got = lessonItems({ keyOf: (w) => w.meaningKey, order: ORDER, all: ALL, seen: new Set(ORDER.map((w) => w.meaningKey)), due: ['gone', 'a'], fresh: 3, size: 3 })
    expect(got.reviews.map((w) => w.meaningKey)).toEqual(['a'])
    expect(got.fresh).toEqual([])
  })
})

describe('weave', () => {
  it('teaches each new item just before asking it, with reviews woven between', () => {
    const cards = weave({ fresh: [ORDER[0], ORDER[1]], reviews: [OUTSIDE] }, {
      teach: (w) => ({ id: `teach:${w.meaningKey}` }),
      asks: (w) => [{ id: `ask:${w.meaningKey}` }],
    })
    expect(cards.map((card) => card.id)).toEqual(['teach:a', 'ask:a', 'ask:z', 'teach:b', 'ask:b'])
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

describe('itemsOf', () => {
  it('marks each item known, learning (met, not known) or new, in the set order', () => {
    const rows = [{ item: 'b', known: true }, { item: 'a', known: false }, { item: 'z', known: true }]
    const got = itemsOf(ORDER.slice(0, 3), (w) => w.meaningKey, rows)
    expect(got.map((one) => [one.key, one.status])).toEqual([['a', 'learning'], ['b', 'known'], ['c', 'new']])
    expect(got[0].item).toBe(ORDER[0])
  })
})
