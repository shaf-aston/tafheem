import { describe, expect, it } from 'vitest'

import dialects from '../../../backend/data/colloquial/dialects.json'
import { project } from '../lib/countryMap'
import shapes from './countryShapes.json'

// The places live in the backend's dialects.json and the outlines here: a code
// with no outline would draw an empty map, a city off its countries a stray dot.
describe('every dialect place has an outline', () => {
  it.each(dialects.dialects.map((d) => [d.key, d]))('%s', (_, d) => {
    d.countries.forEach((code) => expect(shapes.countries[code], code).toBeDefined())
    const boxes = d.countries.map((code) => shapes.countries[code].box)
    d.cities.forEach(({ name, at }) => {
      const [x, y] = project(at)
      expect(boxes.some(([x0, y0, x1, y1]) => x >= x0 && x <= x1 && y >= y0 && y <= y1), name).toBe(true)
    })
  })
})
