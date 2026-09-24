import { describe, expect, it } from 'vitest'

import { nextHeld } from './useArrival'

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
