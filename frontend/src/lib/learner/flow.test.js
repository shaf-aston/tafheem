import { describe, expect, it } from 'vitest'

import { answered, rightOf, screensOf } from './flow'
import { EMPTY, STEPS } from './plan'

const ids = (plan) => screensOf(plan).map((screen) => screen.id)
const CHECK = STEPS.find((step) => step.items)

describe('screensOf', () => {
  it('asks a non-reader only the questions that apply, then shows the plan', () => {
    const list = ids({ ...EMPTY, goals: ['understand'], read: 'no' })
    expect(list).not.toContain('know')
    expect(list).not.toContain('check-0')
    expect(list.at(-1)).toBe('ready')
  })

  it('adds the placement taps and the know question once the learner can read', () => {
    const list = ids({ ...EMPTY, goals: ['understand'], read: 'yes' })
    expect(list.slice(list.indexOf('know'), list.indexOf('know') + 4)).toEqual(['know', 'check-0', 'check-1', 'check-2'])
  })

  it('asks the dialect only of one who wants to speak', () => {
    expect(ids({ ...EMPTY, goals: ['speak'] })).toContain('dialect')
    expect(ids({ ...EMPTY, goals: ['understand'] })).not.toContain('dialect')
  })
})

describe('answered', () => {
  it('needs a pick on a question, at least one on a multi one, and a tap on a tap', () => {
    const [goals, read] = screensOf(EMPTY)
    expect(answered(goals, EMPTY, [])).toBe(false)
    expect(answered(goals, { ...EMPTY, goals: ['speak'] }, [])).toBe(true)
    expect(answered(read, { ...EMPTY, read: 'no' }, [])).toBe(true)
    const tap = { kind: 'tap', index: 1 }
    expect(answered(tap, EMPTY, [0])).toBe(false)
    expect(answered(tap, EMPTY, [0, 2])).toBe(true)
    expect(answered({ kind: 'ready' }, EMPTY, [])).toBe(true)
  })
})

describe('rightOf', () => {
  it('counts the taps that were the right option', () => {
    const rights = CHECK.items.map((item) => item.right)
    expect(rightOf(CHECK, rights)).toBe(CHECK.items.length)
    expect(rightOf(CHECK, [])).toBe(0)
  })
})
