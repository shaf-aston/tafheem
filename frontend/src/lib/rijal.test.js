import { describe, expect, it } from 'vitest'

import { runs, withoutMarks } from './rijal'

describe('runs', () => {
  it('opens on a name at the very start', () => {
    expect(runs('مالك قال', [[0, 4, 7]])).toEqual([{ text: 'مالك', id: 7 }, { text: ' قال' }])
  })

  it('keeps two names side by side apart', () => {
    expect(runs('abcd', [[0, 2, 1], [2, 4, 2]])).toEqual([{ text: 'ab', id: 1 }, { text: 'cd', id: 2 }])
  })

  it('finds the same name twice', () => {
    expect(runs('x ab y ab', [[2, 4, 5], [7, 9, 5]])).toEqual([
      { text: 'x ' }, { text: 'ab', id: 5 }, { text: ' y ' }, { text: 'ab', id: 5 },
    ])
  })

  it('ignores a range outside the string', () => {
    expect(runs('abc', [[10, 14, 3]])).toEqual([{ text: 'abc' }])
  })

  it('counts slices from the piece start when it begins mid-hadith', () => {
    expect(runs('cd ef', [[13, 15, 9]], 10)).toEqual([{ text: 'cd ' }, { text: 'ef', id: 9 }])
  })
})

describe('withoutMarks', () => {
  it('shifts slices left by the direction marks before them', () => {
    expect(withoutMarks('\u200fab \u200fcd', [[5, 7, 1]])).toEqual([[3, 5, 1]])
  })
})
