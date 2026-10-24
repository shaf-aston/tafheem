import { describe, expect, it } from 'vitest'

import { pickRoots } from './rootKey'

describe('pickRoots', () => {
  it('asks about what was typed, never about the first result', () => {
    const { primary } = pickRoots(' كتب ', [{ root: 'ضرب' }])
    expect(primary).toBe('كتب')
  })

  it('offers a different root from the results as an alternate', () => {
    const { alternates } = pickRoots('مكتوب', [{ root: 'كتب' }])
    expect(alternates).toEqual(['كتب'])
  })

  it('does not offer the root that was already asked about', () => {
    const { alternates } = pickRoots('كتب', [{ root: 'كتب' }, { root: 'كتب' }])
    expect(alternates).toEqual([])
  })

  // The nearest case the request does not name: the same root written twice with
  // different hamza. One chip, not two; they are the same question.
  it('treats two spellings of one root as a single alternate', () => {
    const { alternates } = pickRoots('مأمور', [{ root: 'أمر' }, { root: 'امر' }])
    expect(alternates).toEqual(['أمر'])
  })

  // Caught by clicking the real app: the dictionary writes ك-ت-ب where the box
  // held كتب, and the same root was offered back as a second choice.
  it('treats spaced and dashed spellings of one root as the same root', () => {
    expect(pickRoots('كتب', [{ root: 'ك ت ب' }, { root: 'ك-ت-ب' }]).alternates).toEqual([])
  })

  it('caps the chips at three', () => {
    const results = ['كتب', 'ضرب', 'نصر', 'فتح', 'جلس'].map((root) => ({ root }))
    expect(pickRoots('شيء', results).alternates).toHaveLength(3)
  })

  it('survives entries with no root at all', () => {
    expect(pickRoots('من', [{ root: null }, {}, { root: '  ' }]).alternates).toEqual([])
  })

  it('survives no query and no results', () => {
    expect(pickRoots(undefined)).toEqual({ primary: '', alternates: [] })
  })
})
