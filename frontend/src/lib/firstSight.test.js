import { describe, expect, it } from 'vitest'

import { firstSight } from './firstSight'

describe('firstSight', () => {
  it('is true once per key, false after, and keys are independent', () => {
    expect(firstSight('a')).toBe(true)
    expect(firstSight('a')).toBe(false)
    expect(firstSight('b')).toBe(true)
  })
})
