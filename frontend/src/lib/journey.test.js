import { describe, expect, it } from 'vitest'

import { lastOn, nearest, resume, tabNow, trailFor } from './journey'

const STEPS = [
  { tab: 'dict', value: null },
  { tab: 'dict', value: 'كتب' },
  { tab: 'quran', value: '2:255' },
  { tab: 'dict', value: 'book' },
  { tab: 'dict', value: 'سطر' },
]

describe('trailFor', () => {
  it('keeps this tab, in the order walked', () => {
    expect(trailFor(STEPS, 'dict').map((s) => s.value)).toEqual(['كتب', 'book', 'سطر'])
  })

  it('keeps the steps ahead after a step back, they are one click away', () => {
    expect(trailFor(STEPS, 'dict').map((s) => s.index)).toEqual([1, 3, 4])
  })

  it('drops a tab opened with nothing, there is no word to go back to', () => {
    expect(trailFor([STEPS[0]], 'dict')).toEqual([])
  })

  it('carries the index, which is what a click jumps to', () => {
    expect(trailFor(STEPS, 'quran')).toEqual([{ tab: 'quran', value: '2:255', index: 2 }])
  })

  // Dictionary on فهم, a glance at Daleel, back to Dictionary reopened on فهم.
  const RETURN = [
    { tab: 'dict', value: 'فهم' }, { tab: 'daleel', value: null }, { tab: 'dict', value: 'فهم' },
  ]

  it('draws a return to the same word once, as the later step', () => {
    expect(trailFor(RETURN, 'dict', 2).map((s) => s.index)).toEqual([2])
  })

  it('but keeps the earlier one when that is where we are', () => {
    expect(trailFor(RETURN, 'dict', 0).map((s) => s.index)).toEqual([0])
  })
})

describe('nearest', () => {
  // Six words looked up in a row, so the line has to drop some.
  const many = ['a', 'b', 'c', 'd', 'e', 'f'].map((value, index) => ({ tab: 'dict', value, index }))

  it('leaves a short trail alone', () => {
    expect(nearest(many.slice(0, 3), 2, 5)).toEqual({ shown: many.slice(0, 3), sliced: false })
  })

  it('drops the oldest, keeps where we are', () => {
    const { shown, sliced } = nearest(many, 5, 5)
    expect(shown.map((s) => s.value)).toEqual(['b', 'c', 'd', 'e', 'f'])
    expect(sliced).toBe(true)
  })

  it('keeps one step of what is ahead in view', () => {
    expect(nearest(many, 2, 5).shown.map((s) => s.value)).toEqual(['a', 'b', 'c', 'd', 'e'])
  })

  it('never starts before the beginning', () => {
    expect(nearest(many, 0, 5).shown.map((s) => s.value)).toEqual(['a', 'b', 'c', 'd', 'e'])
  })
})

describe('resume', () => {
  const saved = { steps: STEPS, at: 4 }

  it('starts at the address when nothing was saved', () => {
    expect(resume(null, STEPS[1], undefined)).toEqual({ steps: [STEPS[1]], at: 0 })
  })

  it('a reload sits where it was, path intact', () => {
    expect(resume(saved, STEPS[4], 4)).toEqual({ steps: STEPS, at: 4 })
  })

  it('a back press across a reload lands on the step the browser names', () => {
    expect(resume(saved, STEPS[3], 3)).toEqual({ steps: STEPS, at: 3 })
  })

  it('trusts the saved index when the browser has no usable state', () => {
    expect(resume(saved, STEPS[4], undefined)).toEqual({ steps: STEPS, at: 4 })
  })

  it('ignores a state index that does not match the address', () => {
    expect(resume(saved, STEPS[4], 1)).toEqual({ steps: STEPS, at: 4 })
  })

  it('a bare address opens on the last word of that tab, like a bookmark', () => {
    expect(resume(saved, { tab: 'dict', value: null }, undefined)).toEqual({ steps: STEPS, at: 4 })
    expect(resume({ steps: STEPS, at: 3 }, { tab: 'quran', value: null }, undefined))
      .toEqual({ steps: [...STEPS.slice(0, 4), { tab: 'quran', value: '2:255' }], at: 4 })
  })

  it('a bare address on a tab never reached opens blank', () => {
    expect(resume(saved, { tab: 'sarf', value: null }, undefined))
      .toEqual({ steps: [...STEPS, { tab: 'sarf', value: null }], at: 5 })
  })

  it('a pasted link is a new step after the current one, ahead dropped', () => {
    const link = { tab: 'daleel', value: 'patience' }
    expect(resume({ steps: STEPS, at: 2 }, link, undefined))
      .toEqual({ steps: [...STEPS.slice(0, 3), link], at: 3 })
  })
})

describe('lastOn', () => {
  it('is the latest word on that tab at or before here', () => {
    expect(lastOn(STEPS, 4, 'dict')).toBe('سطر')
    expect(lastOn(STEPS, 3, 'dict')).toBe('book')
    expect(lastOn(STEPS, 4, 'quran')).toBe('2:255')
  })

  it('does not count steps ahead, and is null for a tab never reached', () => {
    expect(lastOn(STEPS, 1, 'quran')).toBe(null)
    expect(lastOn(STEPS, 4, 'sarf')).toBe(null)
  })

  it('skips a tab opened with nothing', () => {
    expect(lastOn(STEPS, 0, 'dict')).toBe(null)
  })
})

describe('tabNow', () => {
  it('is the tab of the step the browser sits on', () => {
    expect(tabNow(STEPS, 2)).toBe('quran')
  })

  it('is nothing before the first step is recorded', () => {
    expect(tabNow([], -1)).toBe(null)
  })
})
