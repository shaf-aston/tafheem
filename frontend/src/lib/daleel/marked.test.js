import { describe, expect, it } from 'vitest'

import { markedPieces, withMarks } from './marked'

describe('withMarks → markedPieces', () => {
  it('gives back the marked words and the rest in order', () => {
    expect(markedPieces(withMarks('in the name of God', [[0, 14]]))).toEqual([
      { text: 'in the name of', marked: true },
      { text: ' God', marked: false },
    ])
  })

  it('counts code points, as the server does', () => {
    // 𝒜 is two UTF-16 units but one code point.
    expect(markedPieces(withMarks('𝒜 ما', [[2, 4]]))).toEqual([
      { text: '𝒜 ', marked: false },
      { text: 'ما', marked: true },
    ])
  })

  it('leaves text alone with no marks or bad ones', () => {
    expect(withMarks('كتاب', [])).toBe('كتاب')
    expect(withMarks('كتاب', [[3, 99]])).toBe('كتاب')
    expect(markedPieces('كتاب')).toEqual([{ text: 'كتاب', marked: false }])
  })

  it('survives a reshaping step in between', () => {
    const reshaped = withMarks('a  prayer', [[3, 9]]).replace(/\s+/g, ' ')
    expect(markedPieces(reshaped)).toEqual([
      { text: 'a ', marked: false },
      { text: 'prayer', marked: true },
    ])
  })
})
