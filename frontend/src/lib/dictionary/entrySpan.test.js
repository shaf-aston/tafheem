import { describe, expect, it } from 'vitest'

import { entrySpans } from './entrySpan'

const short = (n) => ({ definitions: Array.from({ length: n }, (_, i) => `sense ${i}`) })
const long = { definitions: ['x'.repeat(130)] }
const syn = { definitions: ['a'], synonyms: [[{ word: 'ب', meaning: '' }]] }
const rowsFull = (spans, cols) => {
  let used = 0
  for (const s of spans) { used += s; if (used > cols) return false; if (used === cols) used = 0 }
  return used === 0
}

describe('entrySpans', () => {
  it('keeps many short senses to one column, so six cards sit in two full rows', () => {
    const six = [short(6), short(2), short(1), short(2), short(2), short(8)]
    expect(entrySpans(six, 3)).toEqual([1, 1, 1, 1, 1, 1])
  })

  it('widens a card whose senses wrap, or that has synonyms', () => {
    expect(entrySpans([long, short(1), short(1), short(1)], 3)).toEqual([2, 1, 2, 1])
    expect(entrySpans([syn, short(1)], 3)[0]).toBe(2)
  })

  it('fills a short row by widening the card that wraps most', () => {
    expect(entrySpans([short(1), long], 3)).toEqual([1, 2])
    expect(entrySpans([short(1)], 3)).toEqual([3])
  })

  it('widens nothing for a single wrapped line', () => {
    expect(entrySpans([short(6), { definitions: ['x'.repeat(54)] }, short(2), short(1), short(2), short(8)], 3))
      .toEqual([1, 1, 1, 1, 1, 1])
  })

  it('evens out rows instead of leaving one card alone', () => {
    expect(entrySpans(Array.from({ length: 7 }, () => short(2)), 3)).toEqual([1, 1, 1, 2, 1, 2, 1])
  })

  it('leaves every row full at any column count', () => {
    const mix = [long, short(3), syn, short(9), long, short(1), short(2)]
    for (const cols of [1, 2, 3]) expect(rowsFull(entrySpans(mix, cols), cols)).toBe(true)
  })
})
