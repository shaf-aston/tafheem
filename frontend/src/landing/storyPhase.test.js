import { describe, expect, it } from 'vitest'

import { locate, sentencePhase } from './storyPhase.js'

const SHAPE = { words: 7, pairs: [{ from: 0, to: 1 }, { from: 3, to: 4 }] }
const KNOBS = { nameShare: 0.4, drawShare: 0.5, whyAt: 0.2 }
const at = (lp) => sentencePhase(lp, SHAPE, KNOBS)

describe('locate', () => {
  it('splits the track by weight', () => {
    const w = [2, 1, 1]
    expect(locate(0, w)).toEqual({ active: 0, lp: 0 })
    expect(locate(0.25, w)).toEqual({ active: 0, lp: 0.5 })
    expect(locate(0.5, w)).toEqual({ active: 1, lp: 0 })
    expect(locate(0.875, w)).toEqual({ active: 2, lp: 0.5 })
  })
  it('ends on the last step at 1, and clamps outside 0 to 1', () => {
    expect(locate(1, [2, 1, 1])).toEqual({ active: 2, lp: 1 })
    expect(locate(-3, [1, 1])).toEqual({ active: 0, lp: 0 })
    expect(locate(9, [1, 1])).toEqual({ active: 1, lp: 1 })
  })
})

describe('sentencePhase', () => {
  it('names the words one by one, the camera on the newest', () => {
    expect(at(0)).toMatchObject({ phase: 'name', named: 0, focus: [0, 0] })
    const mid = at(0.2)
    expect(mid.phase).toBe('name')
    expect(mid.named).toBeGreaterThan(0)
    expect(mid.focus).toEqual([mid.named - 1, mid.named - 1])
    expect(mid.drawn).toEqual([0, 0])
  })
  it('has every word named by the time the arrows start', () => {
    expect(at(0.399).named).toBeLessThanOrEqual(7)
    expect(at(0.4)).toMatchObject({ phase: 'govern', named: 7, pair: 0, focus: [0, 1] })
  })
  it('draws the first pair, then moves on to the second', () => {
    expect(at(0.4).drawn[0]).toBe(0)
    expect(at(0.55).drawn[0]).toBeGreaterThan(0)
    expect(at(0.72)).toMatchObject({ pair: 1, focus: [3, 4] })
    expect(at(0.72).drawn[0]).toBe(1)
    expect(at(1)).toMatchObject({ pair: 1, drawn: [1, 1], why: true })
  })
  it('shows the reason only once a pair has settled', () => {
    expect(at(0.4).why).toBe(false)
    expect(at(0.5).why).toBe(true)
  })
  it('is a pure function of lp, so the same lp gives the same frame in both directions', () => {
    expect(at(0.55)).toEqual(at(0.55))
  })
  it('stays inside the sentence for every lp', () => {
    for (let lp = 0; lp <= 1; lp += 0.01) {
      const p = at(lp)
      p.focus.forEach((i) => { expect(i).toBeGreaterThanOrEqual(0); expect(i).toBeLessThan(7) })
      p.drawn.forEach((d) => { expect(d).toBeGreaterThanOrEqual(0); expect(d).toBeLessThanOrEqual(1) })
    }
  })
})
