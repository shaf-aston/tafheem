import { describe, expect, it } from 'vitest'

import shapes from '../data/countryShapes.json'
import { project, touches, viewOf } from './countryMap'

describe('project', () => {
  it('puts east to the right and north up', () => {
    const [cairoX, cairoY] = project([31.24, 30.04])
    const [rabatX] = project([-6.84, 34.02])
    const [, sanaaY] = project([44.21, 15.37])
    expect(cairoX).toBeGreaterThan(rabatX)
    expect(sanaaY).toBeGreaterThan(cairoY)
  })

  it('lands a capital inside its own outline box', () => {
    const inside = (code, at) => {
      const [x, y] = project(at)
      const [x0, y0, x1, y1] = shapes.countries[code].box
      return x > x0 && x < x1 && y > y0 && y < y1
    }
    expect(inside('EG', [31.24, 30.04])).toBe(true)
    expect(inside('LB', [35.5, 33.89])).toBe(true)
    expect(inside('IQ', [44.36, 33.31])).toBe(true)
  })
})

describe('viewOf', () => {
  it('keeps the aspect asked for', () => {
    const [, , w, h] = viewOf([[0, 0, 300, 100]], [], { aspect: 4 / 3 })
    expect(w / h).toBeCloseTo(4 / 3, 1)
  })

  it('pads a tiny country out to the least width, centred on it', () => {
    const [x, , w] = viewOf([[100, 100, 102, 104]], [], { least: 60, pad: 0 })
    expect(w).toBe(60)
    expect(x + w / 2).toBeCloseTo(101, 1)
  })

  it('takes in a city outside the countries', () => {
    const [x, , w] = viewOf([[0, 0, 100, 100]], [[200, 50]])
    expect(x + w).toBeGreaterThan(200)
  })

  it('is null with nothing to show', () => {
    expect(viewOf([], [])).toBeNull()
  })
})

describe('touches', () => {
  it('says whether a box is in a view', () => {
    expect(touches([10, 10, 20, 20], [0, 0, 15, 15])).toBe(true)
    expect(touches([30, 30, 40, 40], [0, 0, 15, 15])).toBe(false)
  })
})
