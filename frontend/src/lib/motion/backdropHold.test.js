import { describe, expect, it } from 'vitest'

import { heldFor, holdBackdrop } from './backdropHold'

describe('backdropHold', () => {
  it('holds for the time asked, then lets go', () => {
    holdBackdrop(400, 1000)
    expect(heldFor(1100)).toBe(300)
    expect(heldFor(1400)).toBe(0)
  })

  it('a shorter hold does not cut a longer one', () => {
    holdBackdrop(400, 5000)
    holdBackdrop(100, 5000)
    expect(heldFor(5200)).toBe(200)
  })
})
