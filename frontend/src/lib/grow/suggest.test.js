import { describe, expect, it } from 'vitest'

import { bookStep, lessonStep, rankWorlds, scoreOf } from './suggest'

const NOW = Date.parse('2026-10-24T12:00:00Z')
const K = { 'half-life-days': 3, 'level-fit': 1, 'review-at': 4 }
const ago = (days) => new Date(NOW - days * 864e5).toISOString()
const world = (id, more = {}) => ({ id, module: id, name: id.toUpperCase(), live: true, kind: 'book', ...more })
const row = (module, attempts, correct, days) => ({ module, attempts, correct, learnt: 0, lastAt: ago(days) })

describe('scoreOf', () => {
  it('halves a world\'s pull every half-life', () => {
    const today = scoreOf(world('a'), [row('a', 3, 3, 0)], null, NOW, K).score
    const later = scoreOf(world('a'), [row('a', 3, 3, 3)], null, NOW, K).score
    expect(today).toBeCloseTo(2)
    expect(later).toBeCloseTo(1)
  })

  it('pulls up a world being got wrong', () => {
    const right = scoreOf(world('a'), [row('a', 3, 3, 0)], null, NOW, K).score
    const wrong = scoreOf(world('a'), [row('a', 3, 0, 0)], null, NOW, K).score
    expect(wrong).toBeCloseTo(2 * right)
  })

  it('counts every meaning language of a record together', () => {
    const one = scoreOf(world('quiz'), [row('quiz', 3, 3, 0)], null, NOW, K).score
    const both = scoreOf(world('quiz'), [row('quiz', 1, 1, 2), row('quiz:ur', 2, 2, 0)], null, NOW, K).score
    expect(both).toBeCloseTo(one)
  })

  it('a world never used scores only its level fit', () => {
    expect(scoreOf(world('a'), [], 'a', NOW, K)).toEqual({ score: 1, why: 'level' })
    expect(scoreOf(world('a'), [], 'b', NOW, K)).toEqual({ score: 0, why: null })
  })

  it('names the bigger reason', () => {
    expect(scoreOf(world('a'), [row('a', 1, 1, 30)], 'a', NOW, K).why).toBe('level')
    expect(scoreOf(world('a'), [row('a', 7, 7, 0)], 'a', NOW, K).why).toBe('recent')
  })
})

describe('rankWorlds', () => {
  const worlds = [world('a'), world('b'), world('c'), world('off', { live: false })]

  it('puts recent use first, the level next, and leaves out the rest', () => {
    const ranked = rankWorlds(worlds, [row('b', 7, 7, 0), row('off', 50, 50, 0)], 'c', NOW, K)
    expect(ranked.map((one) => one.world.id)).toEqual(['b', 'c'])
  })

  it('lets a few answers yesterday beat the level, and one answer a month ago lose to it', () => {
    expect(rankWorlds(worlds, [row('b', 5, 5, 1)], 'c', NOW, K)[0].world.id).toBe('b')
    expect(rankWorlds(worlds, [row('b', 1, 1, 30)], 'c', NOW, K)[0].world.id).toBe('c')
  })

  it('keeps worlds.json order on a tie, and suggests nothing with no record and no level', () => {
    expect(rankWorlds(worlds, [row('b', 3, 3, 0), row('a', 3, 3, 0)], null, NOW, K).map((one) => one.world.id)).toEqual(['a', 'b'])
    expect(rankWorlds(worlds, [], null, NOW, K)).toEqual([])
  })
})

describe('the step in a world', () => {
  const book = world('fiqh', { name: 'Fiqh' })
  const parts = [{ id: 'tahara', title: 'Purity' }]
  const next = { id: 'wudu', part: 'tahara', title: 'Wudu' }

  it('a book offers its next lesson, named down to it', () => {
    expect(bookStep(book, { parts, next, due: ['x'] }, K)).toEqual({ value: 'fiqh/tahara/wudu', trail: ['Fiqh', 'Purity', 'Wudu'] })
  })

  it('a book offers its review once enough is due, or when nothing else is left', () => {
    expect(bookStep(book, { parts, next, due: ['1', '2', '3', '4'] }, K)).toEqual({ value: 'fiqh/review', trail: ['Fiqh'], due: 4 })
    expect(bookStep(book, { parts, next: null, due: ['1'] }, K)).toEqual({ value: 'fiqh/review', trail: ['Fiqh'], due: 1 })
  })

  it('a finished book with nothing due offers nothing', () => {
    expect(bookStep(book, { parts, next: null, due: [] }, K)).toBeNull()
  })

  it('a lessons world offers its lesson', () => {
    expect(lessonStep(world('basics', { name: 'Basics' }))).toEqual({ value: 'basics/lesson', trail: ['Basics'] })
  })
})
