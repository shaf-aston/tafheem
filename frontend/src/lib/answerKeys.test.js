import { describe, expect, it } from 'vitest'

import { keyAction } from './answerKeys'

describe('keyAction', () => {
  const rule4 = { checked: false, optionCount: 4 }

  it('Enter checks, then moves on', () => {
    expect(keyAction('Enter', rule4)).toEqual({ do: 'check' })
    expect(keyAction('Enter', { ...rule4, checked: true })).toEqual({ do: 'next' })
  })

  it('a flips auto-advance, in either case', () => {
    expect(keyAction('a', rule4)).toEqual({ do: 'auto' })
    expect(keyAction('A', { ...rule4, checked: true })).toEqual({ do: 'auto' })
  })

  it('a digit ticks its option, and only its own digits are ours', () => {
    expect(keyAction('1', rule4)).toEqual({ do: 'toggle', index: 0 })
    expect(keyAction('4', rule4)).toEqual({ do: 'toggle', index: 3 })
    // Past the last option, and on a sentence question, which offers none: not
    // ours, so the digit still reaches the tab shortcuts.
    expect(keyAction('5', rule4)).toBe(null)
    expect(keyAction('1', { checked: false, optionCount: 0 })).toBe(null)
    // The nearest case not asked for: a digit once the answer is on screen must
    // not re-tick an option behind the marks, and must not leave the question.
    expect(keyAction('1', { ...rule4, checked: true })).toEqual({ do: 'swallow' })
    expect(keyAction('0', rule4)).toBe(null)
  })

  it('leaves every other key alone', () => {
    expect(keyAction('b', rule4)).toBe(null)
    expect(keyAction('ArrowRight', rule4)).toBe(null)
    expect(keyAction(' ', rule4)).toBe(null)
    expect(keyAction('Enter')).toEqual({ do: 'check' })
  })
})
