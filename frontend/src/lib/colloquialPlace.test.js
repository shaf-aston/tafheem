import { describe, expect, it } from 'vitest'

import { parsePlace, placeOf } from './colloquialPlace'

const dialects = [{
  key: 'fusha',
  units: [
    { unit: 'unit-01', written: true, lessons: [{ lesson: 'lesson-01', written: true, words: 3 }, { lesson: 'lesson-02', written: false }, { lesson: 'lesson-03', written: true, words: 0 }] },
    { unit: 'unit-02', written: false, lessons: [] },
  ],
}]

describe('parsePlace', () => {
  it('reads a dialect, a unit, and a topic by its position', () => {
    expect(parsePlace('fusha', dialects)).toEqual({ dialect: 'fusha', unit: null, at: null })
    expect(parsePlace('fusha/unit-01', dialects)).toEqual({ dialect: 'fusha', unit: 'unit-01', at: null })
    expect(parsePlace('fusha/unit-01/lesson-01', dialects)).toEqual({ dialect: 'fusha', unit: 'unit-01', at: 0, words: false })
    expect(parsePlace('fusha/unit-01/lesson-01/words', dialects)).toEqual({ dialect: 'fusha', unit: 'unit-01', at: 0, words: true })
  })

  it.each([
    '', null, 'gulf', 'fusha/unit-02', 'fusha/unit-09', 'fusha/unit-01/lesson-02', 'fusha/unit-01/lesson-09', 'fusha/unit-01/lesson-01/x',
    'fusha/unit-01/lesson-03/words', 'fusha/unit-01/lesson-01/words/x',
  ])('refuses %j, so a stale link opens the top', (q) => {
    expect(parsePlace(q, dialects)).toBeNull()
  })

  it('writes back what it reads, at every depth', () => {
    expect(parsePlace(placeOf('fusha'), dialects)?.unit).toBeNull()
    expect(parsePlace(placeOf('fusha', 'unit-01'), dialects)?.unit).toBe('unit-01')
    expect(parsePlace(placeOf('fusha', 'unit-01', 'lesson-01'), dialects)?.at).toBe(0)
    expect(parsePlace(placeOf('fusha', 'unit-01', 'lesson-01', true), dialects)?.words).toBe(true)
  })
})
