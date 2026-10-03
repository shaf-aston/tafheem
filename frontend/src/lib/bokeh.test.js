import { describe, expect, it } from 'vitest'

import { pickColor, seed, seedMarks, step, stepMarks } from './bokeh'

const knobs = { sizeMin: 20, sizeMax: 80, speed: 1, tint: 0.25, colors: ['#a', '#b', '#c'] }
const TAB = '#tab'

describe('seed', () => {
  it('gives n lights inside the box, sized within range', () => {
    const lights = seed(34, 800, 600, knobs)
    expect(lights).toHaveLength(34)
    for (const l of lights) {
      expect(l.x).toBeGreaterThanOrEqual(0)
      expect(l.x).toBeLessThanOrEqual(800)
      expect(l.y).toBeGreaterThanOrEqual(0)
      expect(l.y).toBeLessThanOrEqual(600)
      expect(l.r).toBeGreaterThanOrEqual(20)
      expect(l.r).toBeLessThanOrEqual(80)
    }
  })
})

describe('step', () => {
  it('wraps a light that has fully left the right edge', () => {
    const lights = [{ x: 900, y: 10, r: 50, dx: 1, dy: 0 }]
    step(lights, 800, 600, knobs)
    expect(lights[0].x).toBe(-50)
  })

  it('wraps a light that has fully left the top edge', () => {
    const lights = [{ x: 10, y: -60, r: 50, dx: 0, dy: -1 }]
    step(lights, 800, 600, knobs)
    expect(lights[0].y).toBe(650)
  })

  it('leaves positions alone at speed 0', () => {
    const lights = seed(10, 800, 600, knobs)
    const before = lights.map((l) => [l.x, l.y])
    step(lights, 800, 600, { ...knobs, speed: 0 })
    expect(lights.map((l) => [l.x, l.y])).toEqual(before)
  })
})

describe('pickColor', () => {
  it('never returns the tab colour at tint 0', () => {
    for (let i = 0; i < 200; i++) expect(pickColor(i, { ...knobs, tint: 0 }, TAB)).not.toBe(TAB)
  })

  it('returns the tab colour for about a quarter of lights at tint 0.25', () => {
    const tinted = Array.from({ length: 100 }, (_, i) => pickColor(i, knobs, TAB)).filter((c) => c === TAB)
    expect(tinted.length).toBeGreaterThan(20)
    expect(tinted.length).toBeLessThan(30)
  })
})

describe('marks', () => {
  const mk = { sizeMin: 96, sizeMax: 224, alpha: 0.05, drift: 24, speed: 0.25, letters: ['ع', 'ر', 'ب'] }

  it('seeds count marks inside the box, sized and lettered from the knobs', () => {
    const marks = seedMarks(6, 800, 600, mk)
    expect(marks).toHaveLength(6)
    for (const m of marks) {
      expect(m.x).toBeGreaterThanOrEqual(0)
      expect(m.x).toBeLessThanOrEqual(800)
      expect(m.y).toBeGreaterThanOrEqual(0)
      expect(m.y).toBeLessThanOrEqual(600)
      expect(m.size).toBeGreaterThanOrEqual(96)
      expect(m.size).toBeLessThanOrEqual(224)
      expect(mk.letters).toContain(m.letter)
    }
  })

  it('count 0 seeds nothing', () => {
    expect(seedMarks(0, 800, 600, mk)).toEqual([])
  })

  it('drifts within drift px of home and never changes alpha', () => {
    const marks = seedMarks(6, 800, 600, mk)
    for (let i = 0; i < 500; i++) stepMarks(marks, mk)
    for (const m of marks) {
      expect(Math.abs(m.x - m.hx)).toBeLessThanOrEqual(24)
      expect(Math.abs(m.y - m.hy)).toBeLessThanOrEqual(24)
      expect(m.alpha).toBe(0.05)
    }
  })

  it('stays at home at drift 0', () => {
    const marks = seedMarks(6, 800, 600, mk)
    const before = marks.map((m) => [m.x, m.y])
    stepMarks(marks, { ...mk, drift: 0 })
    expect(marks.map((m) => [m.x, m.y])).toEqual(before)
  })
})
