/**
 * The pinning rule that stops a delayed timings fetch from desyncing an ayah
 * that is already playing. See useRecitedWord.js's own docstring for why this
 * exists; this proves the rule without a browser.
 */
import { describe, expect, it } from 'vitest'

import { pinFor } from './useRecitedWord'

const A = { url: 'everyayah/002200.mp3', segments: [] }
const B = { url: 'quran.com/002200.mp3', segments: [[0, 1, 0, 500]] }
const C = { url: 'quran.com/002201.mp3', segments: [[0, 1, 0, 500]] }

describe('pinFor', () => {
  it('pins the address the moment it is heard playing', () => {
    expect(pinFor(A.url, A, null)).toBe(A)
  })

  it('a request resolving mid-playback does not move the pin', () => {
    // A was pressed and pinned; the fetch then resolves and props flip to B
    // while A is still the address actually sounding.
    expect(pinFor(A.url, B, A)).toBe(A)
  })

  it('nothing pins while props and the playing address disagree from the start', () => {
    expect(pinFor(A.url, B, null)).toBe(null)
  })

  it('a later ayah starting re-pins to it, not the stale one', () => {
    expect(pinFor(C.url, C, A)).toBe(C)
  })
})
