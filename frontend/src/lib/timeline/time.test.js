import { describe, expect, it } from 'vitest'
import { nearest, positions, routeTo, scaleModes, yearTicks } from './time'

const ev = (id, at, place) => ({ id, at, place })
const seerah = { kind: 'dated', events: [ev('birth', 570, 'makkah'), ev('hira', 610, 'hira'), ev('hijrah', 622, 'madinah'), ev('badr', 624, 'badr'), ev('khandaq', 627, 'madinah'), ev('end', 630, 'madinah')] }

describe('time bar', () => {
  it('offers true years only where at is a year', () => {
    expect(scaleModes(seerah)).toEqual(['years', 'even'])
    expect(scaleModes({ kind: 'undated', events: [] })).toEqual(['even'])
  })

  it('keeps the real gaps in years and equal room in even steps', () => {
    expect(positions(seerah, 'years')[1]).toBeCloseTo(40 / 60)
    expect(positions(seerah, 'even')).toEqual([0, 0.2, 0.4, 0.6, 0.8, 1])
    expect(positions({ events: [ev('a', 5)] }, 'years')).toEqual([0])
  })

  it('finds the nearest event to a point, the earlier on a tie', () => {
    expect(nearest([0, 0.5, 1], 0.7)).toBe(1)
    expect(nearest([0, 0.5, 1], 0.25)).toBe(0)
  })

  it('marks round years inside the span, never more than the cap', () => {
    const ticks = yearTicks(seerah)
    expect(ticks[0]).toEqual({ year: 570, at: 0 })
    expect(ticks.at(-1).year).toBe(630)
    expect(ticks.length).toBeLessThanOrEqual(8)
  })

  it('walks the places in order, a stay in one place counted once', () => {
    expect(routeTo(seerah, 2)).toEqual(['makkah', 'hira', 'madinah'])
    expect(routeTo(seerah, 5)).toEqual(['makkah', 'hira', 'madinah', 'badr', 'madinah'])
    expect(routeTo({ events: [ev('a', 1, null), ev('b', 2, 'x')] }, 1)).toEqual(['x'])
  })
})
