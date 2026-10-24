import { describe, expect, it } from 'vitest'

import { estimate, fitLabel, namesOf, wrap } from './pbsFit'

const half = (text) => text.length * 0.5 // a letter is half an em wide, a space too

describe('wrap', () => {
  it('keeps a label that fits on one line', () => {
    expect(wrap('abc def', 10, half)).toEqual(['abc def'])
  })

  it('breaks between words, never inside one, and keeps every line within the room', () => {
    const lines = wrap('aaaa bbbb cccc dddd eeee', 6, half)
    expect(lines.join(' ')).toBe('aaaa bbbb cccc dddd eeee')
    for (const line of lines) expect(half(line)).toBeLessThanOrEqual(6)
  })

  it('takes the fewest lines, and spreads the words evenly over them', () => {
    // Greedy would be "aaa bbb ccc ddd" over "eee"; two lines is the least, and even is "aaa bbb ccc" / "ddd eee".
    expect(wrap('aaa bbb ccc ddd eee', 8, half)).toEqual(['aaa bbb ccc', 'ddd eee'])
  })

  it('lets a word wider than the room stand alone', () => {
    expect(wrap('ab longlonglong cd', 3, half)).toEqual(['ab', 'longlonglong', 'cd'])
  })

  it('draws nothing for nothing', () => {
    expect(wrap('', 5, half)).toEqual([])
    expect(wrap('   ', 5, half)).toEqual([])
  })
})

describe('fitLabel', () => {
  it('draws at its own size when its lines fit', () => {
    expect(fitLabel('aaa bbb ccc', { room: 100, size: 10 }, half)).toEqual({ lines: ['aaa bbb ccc'], size: 10 })
  })

  it('wraps a long label and keeps its size', () => {
    const { lines, size } = fitLabel('aaa bbb ccc ddd eee', { room: 40, size: 10 }, half)
    expect(lines.length).toBeGreaterThan(1)
    expect(size).toBe(10)
  })

  it('shrinks only for a single word that is wider than the room', () => {
    const { lines, size } = fitLabel('abcdefghij', { room: 25, size: 10 }, half) // 50 wide at size 10
    expect(lines).toEqual(['abcdefghij'])
    expect(size).toBe(5)
  })
})

describe('estimate', () => {
  it('counts letters and spaces but not vowel signs', () => {
    expect(estimate('ب ب')).toBe(estimate('بَ بِ'))
    expect(estimate('')).toBe(0)
  })
})

describe('namesOf', () => {
  it('lists the root, every branch and every kid', () => {
    const config = { root: { ar: 'ر' }, branches: [{ ar: 'أ', kids: [['ب', 'b'], ['ج', 'c']] }, { ar: 'د', kids: [] }] }
    expect(namesOf(config)).toBe('ر أ ب ج د')
  })
})
