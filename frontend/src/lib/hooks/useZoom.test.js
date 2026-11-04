import { describe, expect, it } from 'vitest'

import { steppedZoom } from './useZoom'

const knobs = { min: 0.7, max: 3, step: 0.2 }

describe('steppedZoom', () => {
  it('moves one step in or out without drifting', () => {
    expect(steppedZoom(1, 1, knobs)).toBe(1.2)
    expect(steppedZoom(0.7, 1, knobs)).toBe(0.9)
    expect(steppedZoom(1.2, -1, knobs)).toBe(1)
  })

  it('stops at the ends', () => {
    expect(steppedZoom(0.7, -1, knobs)).toBe(0.7)
    expect(steppedZoom(2.9, 1, knobs)).toBe(3)
    expect(steppedZoom(3, 1, knobs)).toBe(3)
  })
})
