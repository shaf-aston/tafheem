import { describe, expect, it } from 'vitest'

import { LEAST_TALL, RAIL, anchorOf, placeInRail, railView } from './labelRail'

const view = [0, 0, 300, 400]

describe('the label rail: every board says its tapped word in the same place', () => {
  it('widens the view on the right only, by the rail', () => {
    expect(railView(view)).toEqual([0, 0, 300 * (1 + RAIL), 400])
    expect(railView([10, 20, 100, 50]).slice(0, 2)).toEqual([10, 20])
  })

  it('gives a strip of tiles room below it, so a label fits beside its tiles', () => {
    const strip = [0, 0, 350, 72]
    const [, , w, h] = railView(strip)
    expect(h).toBeCloseTo(w * LEAST_TALL)
    const at = placeInRail(strip, { area: [300, 0, 50, 72] }, 100)
    expect(at.y + 100).toBeLessThanOrEqual(h)                        // inside the picture, not spilling off it
  })

  it('stands the word in the rail, beyond the drawing, inside the widened picture', () => {
    for (const spot of [{ x: 10, y: 200 }, { x: 290, y: 5 }, { area: [0, 0, 100, 100] }, { area: [200, 300, 100, 100] }]) {
      const at = placeInRail(view, spot, 60)
      expect(at.x).toBeGreaterThan(300)                                   // never on the drawing
      expect(at.x + at.w).toBeLessThan(railView(view)[2])                 // never out of the picture
      expect(at.y).toBeGreaterThanOrEqual(0)
      expect(at.y + 60).toBeLessThanOrEqual(400)
    }
  })

  it('stands level with its place, and joins its line to the label’s near edge', () => {
    const at = placeInRail(view, { x: 120, y: 200 }, 60)
    expect(at.y + 30).toBe(200)
    expect(at.line).toEqual({ x: at.x, y: 200 })
  })

  it('a place near the top or the bottom keeps its word inside, the line still on the label', () => {
    const high = placeInRail(view, { x: 120, y: 2 }, 60)
    const low = placeInRail(view, { x: 120, y: 398 }, 60)
    expect(high.y).toBe(0)
    expect(low.y).toBe(340)
    expect(high.line.y).toBeGreaterThanOrEqual(high.y)
    expect(low.line.y).toBeLessThanOrEqual(low.y + 60)
  })

  it('anchors a dot at its centre and an area at the middle of its right edge', () => {
    expect(anchorOf({ x: 5, y: 6 })).toEqual({ x: 5, y: 6 })
    expect(anchorOf({ area: [10, 20, 30, 40] })).toEqual({ x: 40, y: 40 })
  })
})
