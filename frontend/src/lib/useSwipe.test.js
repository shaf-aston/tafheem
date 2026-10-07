import { describe, expect, it } from 'vitest'

import { swipeOf } from './useSwipe'

describe('swipeOf', () => {
  it('goes next on a swipe left and back on a swipe right', () => {
    expect(swipeOf({ dx: -100, dy: 5 })).toBe(1)
    expect(swipeOf({ dx: 100, dy: 5 })).toBe(-1)
  })

  it('ignores a short drag and a mostly vertical one', () => {
    expect(swipeOf({ dx: -30, dy: 0 })).toBe(0)
    expect(swipeOf({ dx: -100, dy: 80 })).toBe(0)
  })

  it('takes a quick mouse flick but leaves a slow mouse drag to text selection', () => {
    expect(swipeOf({ dx: -100, dy: 0, ms: 150, mouse: true })).toBe(1)
    expect(swipeOf({ dx: -100, dy: 0, ms: 600, mouse: true })).toBe(0)
    expect(swipeOf({ dx: -100, dy: 0, ms: 600 })).toBe(1)
  })
})
