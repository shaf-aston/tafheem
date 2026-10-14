import { describe, expect, it } from 'vitest'

import { starsOf } from './sky'

describe('starsOf', () => {
  it('is the same every time for one seed, and differs between seeds', () => {
    expect(starsOf(7, 1)).toEqual(starsOf(7, 1))
    expect(starsOf(7, 1)).not.toEqual(starsOf(7, 2))
  })

  it('gives one star per ayah, inside the box, none closer than 8', () => {
    for (let count = 1; count <= 11; count += 1) {
      for (let seed = 1; seed <= 30; seed += 1) {
        const stars = starsOf(count, seed)
        expect(stars).toHaveLength(count)
        for (const { x, y } of stars) {
          expect(x).toBeGreaterThanOrEqual(0)
          expect(x).toBeLessThanOrEqual(100)
          expect(y).toBeGreaterThanOrEqual(0)
          expect(y).toBeLessThanOrEqual(60)
        }
        for (let a = 0; a < count; a += 1) {
          for (let b = a + 1; b < count; b += 1) {
            expect(Math.hypot(stars[a].x - stars[b].x, stars[a].y - stars[b].y)).toBeGreaterThanOrEqual(8)
          }
        }
      }
    }
  })

  it('reads right to left: the first ayah is the rightmost star', () => {
    const stars = starsOf(7, 3)
    expect(stars[0].x).toBeGreaterThan(stars[6].x)
    expect(stars[0].x).toBeGreaterThan(stars[1].x)
  })
})
