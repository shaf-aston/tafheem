import { describe, expect, it } from 'vitest'

import { apca } from './tone'

describe('apca', () => {
  it('matches the published pairs', () => {
    expect(apca('#888888', '#ffffff')).toBeCloseTo(63.1, 0)
    expect(apca('#ffffff', '#000000')).toBeCloseTo(-107.9, 0)
  })

  it('is positive for dark on light, negative for light on dark, zero for equal', () => {
    expect(apca('#000000', '#ffffff')).toBeGreaterThan(100)
    expect(apca('#336699', '#336699')).toBe(0)
  })

  it('is zero for greys too close to tell apart, below the noise floor', () => {
    expect(apca('#777777', '#787878')).toBe(0)
    expect(apca('#111111', '#222222')).toBe(0)
  })

  it('weighs blue and red as the published pairs do', () => {
    expect(apca('#0000ff', '#ffffff')).toBeCloseTo(85.8, 0)
    expect(apca('#ff0000', '#ffffff')).toBeCloseTo(64.1, 0)
  })
})
