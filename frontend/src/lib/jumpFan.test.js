import { describe, expect, it } from 'vitest'

import { landing, pickAt } from './jumpFan'

const BOXES = [
  { id: 'top', top: 100, bottom: 130 },
  { id: 'back', top: 136, bottom: 166 },
  { id: 'bottom', top: 172, bottom: 202 },
]

describe('the jump fan', () => {
  it('lights the choice under the finger, or the nearest one above the bar', () => {
    expect(pickAt(150, BOXES)).toBe('back')
    expect(pickAt(20, BOXES)).toBe('top')
    expect(pickAt(133, BOXES)).toBe('top')
  })

  it('lights nothing once the finger is back below the fan', () => {
    expect(pickAt(260, BOXES)).toBeNull()
    expect(pickAt(150, [])).toBeNull()
  })

  it('lands on the top, the saved place, or the end', () => {
    expect(landing('top', 900, 4000)).toBe(0)
    expect(landing('back', 900, 4000)).toBe(900)
    expect(landing('bottom', 900, 4000)).toBe(4000)
  })
})
