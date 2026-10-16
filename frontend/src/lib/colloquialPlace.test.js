import { describe, expect, it } from 'vitest'

import { nameOfPlace, parsePlace, placeOf, switchPlace, trailOf, unitNumber } from './colloquialPlace'

const dialects = [{
  key: 'fusha',
  label: 'Fusha',
  units: [
    { unit: 'unit-01', title: 'Meeting', written: true, lessons: [{ lesson: 'lesson-01', title: 'Greetings', written: true, words: 3 }, { lesson: 'lesson-02', written: false }, { lesson: 'lesson-03', written: true, words: 0 }, { lesson: 'lesson-04', title: 'Food', written: true, words: 2 }] },
    { unit: 'unit-02', written: false, lessons: [] },
  ],
}, {
  // Wrote lesson 1 with no word list, left 2 and 3 unwritten, and wrote lesson 4 as fusha did.
  key: 'gulf',
  label: 'Gulf',
  units: [
    { unit: 'unit-01', title: 'Meeting', written: true, lessons: [{ lesson: 'lesson-01', written: true, words: 0 }, { lesson: 'lesson-02', written: false }, { lesson: 'lesson-03', written: false }, { lesson: 'lesson-04', written: true, words: 2 }] },
  ],
}, {
  key: 'levant',
  label: 'Levant',
  units: [{ unit: 'unit-01', title: 'Meeting', written: false, lessons: [] }],
}]

describe('parsePlace', () => {
  it('reads a dialect, a unit, and a topic by its position', () => {
    expect(parsePlace('fusha', dialects)).toEqual({ dialect: 'fusha', unit: null, at: null })
    expect(parsePlace('fusha/unit-01', dialects)).toEqual({ dialect: 'fusha', unit: 'unit-01', at: null })
    expect(parsePlace('fusha/unit-01/lesson-01', dialects)).toEqual({ dialect: 'fusha', unit: 'unit-01', at: 0, words: false })
    expect(parsePlace('fusha/unit-01/lesson-01/words', dialects)).toEqual({ dialect: 'fusha', unit: 'unit-01', at: 0, words: true })
  })

  it.each([
    '', null, 'khaleeji', 'fusha/unit-02', 'fusha/unit-09', 'fusha/unit-01/lesson-02', 'fusha/unit-01/lesson-09', 'fusha/unit-01/lesson-01/x',
    'fusha/unit-01/lesson-03/words', 'fusha/unit-01/lesson-01/words/x',
  ])('refuses %j, so a stale link opens the top', (q) => {
    expect(parsePlace(q, dialects)).toBeNull()
  })

})

describe('placeOf', () => {
  it.each([
    'fusha', 'fusha/unit-01', 'fusha/unit-01/lesson-01', 'fusha/unit-01/lesson-01/words', 'fusha/unit-01/lesson-04',
  ])('writes back what parsePlace read: %s', (q) => {
    expect(placeOf(parsePlace(q, dialects), dialects)).toBe(q)
  })

  it('writes the top as null, and a topic by its lesson key', () => {
    expect(placeOf(null, dialects)).toBeNull()
    expect(placeOf({ dialect: 'fusha', unit: 'unit-01', at: 3, words: false }, dialects)).toBe('fusha/unit-01/lesson-04')
  })
})

describe('unitNumber', () => {
  it('reads the number in a unit id', () => {
    expect(unitNumber('unit-07')).toBe(7)
    expect(unitNumber('intro')).toBe(0)
  })
})

describe('switchPlace', () => {
  it('keeps the unit, the topic and the words where the other dialect has written them', () => {
    expect(switchPlace({ dialect: 'fusha', unit: 'unit-01', at: 3, words: true }, 'gulf', dialects))
      .toEqual({ dialect: 'gulf', unit: 'unit-01', at: 3, words: true })
  })
  it('lands on the unit list when the dialect has not written the unit', () => {
    expect(switchPlace({ dialect: 'fusha', unit: 'unit-01', at: 0, words: true }, 'levant', dialects))
      .toEqual({ dialect: 'levant', unit: null, at: null, words: false })
  })
  it('lands on the topic list when the dialect has not written the topic', () => {
    expect(switchPlace({ dialect: 'fusha', unit: 'unit-01', at: 2, words: false }, 'gulf', dialects))
      .toEqual({ dialect: 'gulf', unit: 'unit-01', at: null, words: false })
  })
  it('keeps the topic but drops the words view when the topic has no words there', () => {
    expect(switchPlace({ dialect: 'fusha', unit: 'unit-01', at: 0, words: true }, 'gulf', dialects))
      .toEqual({ dialect: 'gulf', unit: 'unit-01', at: 0, words: false })
  })
  it('keeps a place above the topic as it is', () => {
    expect(switchPlace({ dialect: 'fusha', unit: 'unit-01', at: null }, 'gulf', dialects))
      .toEqual({ dialect: 'gulf', unit: 'unit-01', at: null, words: false })
  })
})

describe('trailOf', () => {
  it('is only the top at the top', () => {
    expect(trailOf(null, dialects)).toEqual([{ label: 'Dialects', place: null }])
  })
  it('goes from the top to the current place, each step naming where it leads', () => {
    const here = { dialect: 'fusha', unit: 'unit-01', at: 0, words: true }
    const steps = trailOf(here, dialects)
    expect(steps.map((s) => s.label)).toEqual(['Dialects', 'Fusha', 'Unit 1', 'Greetings', 'Words'])
    expect(steps.map((s) => placeOf(s.place, dialects))).toEqual([
      null, 'fusha', 'fusha/unit-01', 'fusha/unit-01/lesson-01', 'fusha/unit-01/lesson-01/words',
    ])
    expect(steps.at(-1).place).toBe(here)
  })
  it('stops at the topic when the words are not open', () => {
    expect(trailOf({ dialect: 'fusha', unit: 'unit-01', at: 0, words: false }, dialects).map((s) => s.label))
      .toEqual(['Dialects', 'Fusha', 'Unit 1', 'Greetings'])
  })
})

describe('nameOfPlace', () => {
  it('names a place in words, and leaves a stale one as it was', () => {
    expect(nameOfPlace('fusha', dialects)).toBe('Fusha')
    expect(nameOfPlace('fusha/unit-01', dialects)).toBe('Meeting')
    expect(nameOfPlace('fusha/unit-01/lesson-01', dialects)).toBe('Greetings')
    expect(nameOfPlace('fusha/unit-01/lesson-01/words', dialects)).toBe('Greetings: words')
    expect(nameOfPlace('khaleeji/unit-01', dialects)).toBe('khaleeji/unit-01')
  })
})
