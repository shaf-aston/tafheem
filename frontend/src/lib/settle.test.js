import { describe, expect, it, vi } from 'vitest'

import { finishEntrances } from './settle'

const animation = (endTime) => ({ effect: { getComputedTiming: () => ({ endTime }) }, finish: vi.fn() })

describe('finishEntrances', () => {
  it('finishes the entrances and leaves the loops running', () => {
    const rise = animation(420)
    const shimmer = animation(Infinity)
    finishEntrances({ getAnimations: () => [rise, shimmer] })
    expect(rise.finish).toHaveBeenCalledOnce()
    expect(shimmer.finish).not.toHaveBeenCalled()
  })

  it('does nothing without a panel', () => {
    expect(() => finishEntrances(null)).not.toThrow()
  })
})
