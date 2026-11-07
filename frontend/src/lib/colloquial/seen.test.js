// @vitest-environment happy-dom
import { beforeEach, describe, expect, it } from 'vitest'

import { forgetSeen, isSeen, markSeen, seenInUnit, topicOf } from './seen'

const read = () => JSON.parse(localStorage.getItem('colloq-seen'))

describe('seen topics', () => {
  beforeEach(() => forgetSeen())

  it('a topic is the first three pieces of a place; above that there is none', () => {
    expect(topicOf('egyptian/unit-01/lesson-02/words')).toBe('egyptian/unit-01/lesson-02')
    expect(topicOf('egyptian/unit-01')).toBeNull()
    expect(topicOf(null)).toBeNull()
  })

  it('opening a topic marks it once, and remembers the place it was opened at', () => {
    markSeen('egyptian/unit-01/lesson-02')
    markSeen('egyptian/unit-01/lesson-02/words')
    expect(read()).toEqual({ last: 'egyptian/unit-01/lesson-02/words', seen: ['egyptian/unit-01/lesson-02'] })
  })

  it('opening a dialect or unit is not opening a topic', () => {
    markSeen('egyptian')
    markSeen('egyptian/unit-01')
    expect(localStorage.getItem('colloq-seen')).toBeNull()
  })

  it('counts a unit\'s topics and not another dialect\'s', () => {
    markSeen('egyptian/unit-01/lesson-01')
    markSeen('egyptian/unit-01/lesson-03')
    markSeen('gulf/unit-01/lesson-01')
    const record = read()
    expect(seenInUnit(record, 'egyptian', 'unit-01')).toBe(2)
    expect(seenInUnit(record, 'egyptian', 'unit-02')).toBe(0)
    expect(isSeen(record, 'gulf', 'unit-01', 'lesson-01')).toBe(true)
    expect(isSeen(record, 'gulf', 'unit-01', 'lesson-02')).toBe(false)
  })
})
