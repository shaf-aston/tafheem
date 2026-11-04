import { describe, expect, it, vi } from 'vitest'

import { replay } from './replay'

describe('replay', () => {
  it('rewinds every animation on the element, with no delay, and plays it', () => {
    const one = { effect: { updateTiming: vi.fn() }, currentTime: 900, play: vi.fn() }
    replay({ getAnimations: () => [one] })
    expect(one.effect.updateTiming).toHaveBeenCalledWith({ delay: 0 })
    expect(one.currentTime).toBe(0)
    expect(one.play).toHaveBeenCalled()
  })

  it('does nothing where the browser has no animations to give (or no element)', () => {
    expect(() => replay({})).not.toThrow()
    expect(() => replay(null)).not.toThrow()
  })
})
