import { describe, expect, it } from 'vitest'

import { isDue, nextHeld } from './useArrival'

describe('nextHeld', () => {
  it('shows the answer that came back', () => {
    expect(nextHeld(null, { root: 'فهم' }, false)).toEqual({ root: 'فهم' })
  })

  it('keeps the last answer while a return is being fetched', () => {
    const shown = nextHeld(null, { root: 'فهم' }, false)
    expect(nextHeld(shown, undefined, true)).toEqual({ root: 'فهم' })
  })

  it('clears it for a search the reader typed, which is a new question', () => {
    const shown = nextHeld(null, { root: 'فهم' }, false)
    expect(nextHeld(shown, undefined, false)).toBe(null)
  })

  it('drops it once the return has stopped without an answer', () => {
    expect(nextHeld({ root: 'فهم' }, undefined, false)).toBe(null)
  })

  it('keeps nothing when there was nothing to keep', () => {
    expect(nextHeld(null, undefined, true)).toBe(null)
  })

  // The nearest case the flash does not name: going back to the word already on
  // screen. The panel's own searches are steps too, so this is a real return,
  // and the answer must not blink for it either.
  it('holds the same answer through a return to the word already shown', () => {
    const answer = { root: 'فهم' }
    const shown = nextHeld(null, answer, false)
    expect(nextHeld(shown, undefined, true)).toBe(answer)
    expect(nextHeld(shown, answer, false)).toBe(answer)
  })
})

describe('isDue', () => {
  it('waits for the data, then takes the arrival once', () => {
    expect(isDue(undefined, 3, false)).toBe(false)
    expect(isDue(undefined, 3, true)).toBe(true)
    expect(isDue(3, 3, true)).toBe(false)
  })

  it('takes the first arrival even when it is null', () => {
    expect(isDue(undefined, null, true)).toBe(true)
  })

  it('follows a repeat arrival of the same word, which has a new number', () => {
    expect(isDue(3, 4, true)).toBe(true)
  })
})
