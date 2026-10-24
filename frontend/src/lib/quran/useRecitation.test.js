/**
 * Which word is lit at a given moment.
 *
 * The rest of the feature is a fetch and a class name; this is the only place a
 * decision is made, and getting it wrong lights the wrong word, which is worse
 * than lighting none.
 */
import { describe, expect, it } from 'vitest'

import { wordAt } from './useRecitation'

// Ayat al-Kursi's opening, as api.quran.com gives it:
// [order, word number, starts at ms, ends in ms].
const SEGMENTS = [
  [0, 1, 40, 980],
  [1, 2, 990, 1040],
  [2, 3, 1050, 3450],
]

describe('wordAt', () => {
  it('counts from zero, because the page draws words from zero', () => {
    expect(wordAt(SEGMENTS, 500)).toBe(0)
    expect(wordAt(SEGMENTS, 1000)).toBe(1)
    expect(wordAt(SEGMENTS, 2000)).toBe(2)
  })

  it('lights a word the moment it starts and not once it has ended', () => {
    expect(wordAt(SEGMENTS, 40)).toBe(0)
    expect(wordAt(SEGMENTS, 979)).toBe(0)
    expect(wordAt(SEGMENTS, 980)).toBe(-1)
  })

  it('lights nothing in the silence before the first word', () => {
    expect(wordAt(SEGMENTS, 0)).toBe(-1)
  })

  it('lights nothing in the gap between two words, rather than holding the last', () => {
    expect(wordAt(SEGMENTS, 985)).toBe(-1)
  })

  it('lights nothing after the last word, so an ayah does not end lit', () => {
    expect(wordAt(SEGMENTS, 99000)).toBe(-1)
  })

  it('lights nothing when no times were measured at all', () => {
    expect(wordAt([], 1000)).toBe(-1)
  })
})
