import { describe, expect, it } from 'vitest'

import { burst, ration } from './fahm'

const fixed = (n) => () => n

describe('ration', () => {
  it('says yes on the drawn call, then counts again from zero', () => {
    const party = ration({ min: 2, max: 4 }, fixed(0.5))
    expect([party(), party(), party(), party(), party(), party()]).toEqual([false, false, true, false, false, true])
  })

  it('never fires sooner than min or later than max', () => {
    const soonest = ration({ min: 2, max: 4 }, fixed(0))
    expect([soonest(), soonest()]).toEqual([false, true])
    const latest = ration({ min: 2, max: 4 }, fixed(0.999))
    expect([latest(), latest(), latest(), latest()]).toEqual([false, false, false, true])
  })
})

describe('burst', () => {
  it('carries all four marks and flies upward from near its origin', () => {
    const bits = burst({ count: 8, x: 160, y: 104, spread: 30 }, fixed(0.5))
    expect(new Set(bits.map((b) => b.kind))).toEqual(new Set([0, 1, 2, 3]))
    for (const b of bits) {
      expect(b.dy).toBeLessThan(0)
      expect(Math.abs(b.x - 160)).toBeLessThanOrEqual(30)
    }
  })
})
