import { describe, expect, it } from 'vitest'

import { anchoredScroll, pinchedZoom } from './usePinch'

describe('anchoredScroll', () => {
  it('keeps the point under the fingers in place as the content grows', () => {
    // 100px scrolled, fingers 50px in: that spot is 150px into the content, 300px once doubled
    expect(anchoredScroll(100, 50, 2)).toBe(250)
    expect(anchoredScroll(250, 50, 0.5)).toBe(100)
  })

  it('leaves the scroll alone when the zoom does not change', () => {
    expect(anchoredScroll(120, 40, 1)).toBe(120)
  })
})

describe('pinchedZoom', () => {
  it('scales the zoom by the spread and holds it within its limits', () => {
    expect(pinchedZoom(1, 1.5, 0.7, 3)).toBe(1.5)
    expect(pinchedZoom(2.5, 2, 0.7, 3)).toBe(3)
    expect(pinchedZoom(1, 0.1, 0.7, 3)).toBe(0.7)
  })
})
