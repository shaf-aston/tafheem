import { describe, expect, it } from 'vitest'

import { markedRuns } from './familyWords'

describe('markedRuns', () => {
  it('sets each marked word apart and joins the words between', () => {
    const runs = markedRuns('a b c d e', [{ at: 1, kind: 'only', other: '' }, { at: 3, kind: 'dots', other: 'x' }])
    expect(runs).toEqual([
      { text: 'a' }, { text: 'b', kind: 'only', other: '' }, { text: 'c' }, { text: 'd', kind: 'dots', other: 'x' }, { text: 'e' },
    ])
  })

  it('reads the matn the way the build did, on any run of whitespace', () => {
    expect(markedRuns(' a  b\n', [{ at: 1, kind: 'only', other: '' }]).map((r) => r.text)).toEqual(['a', 'b'])
  })

  it('is the whole text in one run when nothing is marked', () => {
    expect(markedRuns('a b c', [])).toEqual([{ text: 'a b c' }])
  })
})
