import { describe, expect, it } from 'vitest'

import { MAX_WIDTH, MIN_WIDTH, placeCallout } from './calloutPlace'

// A figure in the middle of a 448 x 690 box, with 93px of margin on the left and 74px on the right:
// the outfit board at its usual size.
const box = { w: 448, h: 690 }
const art = { x0: 93, y0: 20, x1: 374, y1: 670 }
const height = 48
const at = (x, y) => ({ x, y, r: 10 })
const inside = (p) => p.x >= 0 && p.x + p.w <= box.w && p.y >= 0 && p.y + height <= box.h
const clear = (p, a = art) => p.x + p.w <= a.x0 || p.x >= a.x1

describe('placeCallout: the label stands in the margin, never on the drawing', () => {
  it('stands against the drawing on the side nearer the dot, with a gap, inside the box', () => {
    const left = placeCallout({ box, art, dot: at(120, 300), height })
    expect(left.side).toBe('left')
    expect(left.x + left.w).toBeLessThan(art.x0)
    expect(inside(left)).toBe(true)

    const right = placeCallout({ box, art, dot: at(340, 300), height })
    expect(right.side).toBe('right')
    expect(right.x).toBeGreaterThan(art.x1)
    expect(inside(right)).toBe(true)
  })

  it('is as wide as the margin allows, between the least a word needs and the most it is worth', () => {
    const p = placeCallout({ box, art, dot: at(120, 300), height })
    expect(p.w).toBeGreaterThanOrEqual(MIN_WIDTH)
    expect(p.w).toBeLessThanOrEqual(MAX_WIDTH)
    const wide = placeCallout({ box: { w: 900, h: 690 }, art: { ...art, x0: 400, x1: 700 }, dot: at(420, 300), height })
    expect(wide.w).toBe(MAX_WIDTH)
  })

  it('stays on the side the dot is nearer to: the far side would run its line across the whole figure', () => {
    // 20px of margin on the left is too little; the right has room, but the dot is on the left.
    expect(placeCallout({ box, art: { ...art, x0: 20 }, dot: at(60, 300), height })).toBeNull()
  })

  it('has no place when the drawing fills its box: the words stay in the card', () => {
    expect(placeCallout({ box, art: { x0: 0, y0: 0, x1: 448, y1: 690 }, dot: at(200, 300), height })).toBeNull()
    expect(placeCallout({ box, art: { x0: 10, y0: 0, x1: 440, y1: 690 }, dot: at(200, 300), height })).toBeNull()
  })

  it('has no place when neither margin is wide enough for a word', () => {
    expect(placeCallout({ box, art: { ...art, x0: 60, x1: 390 }, dot: at(200, 300), height })).toBeNull()
  })

  it('keeps the label inside the box when the dot is at the top or the bottom', () => {
    const high = placeCallout({ box, art, dot: at(120, 6), height })
    const low = placeCallout({ box, art, dot: at(120, 686), height })
    expect(inside(high)).toBe(true)
    expect(inside(low)).toBe(true)
    // ...and the line still reaches the label's edge, level with the dot as far as the label allows.
    expect(high.line.y).toBeGreaterThanOrEqual(high.y)
    expect(high.line.y).toBeLessThanOrEqual(high.y + height)
  })

  it('draws its line to the edge of the label that faces the drawing', () => {
    const left = placeCallout({ box, art, dot: at(120, 300), height })
    expect(left.line.x).toBe(left.x + left.w)
    const right = placeCallout({ box, art, dot: at(340, 300), height })
    expect(right.line.x).toBe(right.x)
  })

  it('will not stand over another dot, over an area, or over another dot’s line out to its place', () => {
    const dot = at(120, 300)
    expect(placeCallout({ box, art, dot, height })).not.toBeNull()
    expect(placeCallout({ box, art, dot, height, others: [at(40, 310)] })).toBeNull()
    expect(placeCallout({ box, art, dot, height, others: [{ x0: 10, y0: 280, x1: 80, y1: 340 }] })).toBeNull()
    expect(placeCallout({ box, art, dot, height, lines: [{ x0: 150, y0: 300, x1: 20, y1: 310 }] })).toBeNull()
    // Elsewhere in the margin, it is fine.
    expect(placeCallout({ box, art, dot, height, others: [at(40, 600)], lines: [{ x0: 150, y0: 600, x1: 20, y1: 640 }] })).not.toBeNull()
  })

  it('does not stand on its own dot, when that dot is out in the margin', () => {
    expect(placeCallout({ box, art, dot: at(50, 300), height })).toBeNull()
  })

  it('gives up on a label taller than the box', () => {
    expect(placeCallout({ box: { w: 448, h: 40 }, art, dot: at(120, 20), height })).toBeNull()
  })

  it('answers null for anything it was not given, rather than guessing', () => {
    expect(placeCallout({ box: null, art, dot: at(1, 1), height })).toBeNull()
    expect(placeCallout({ box, art: null, dot: at(1, 1), height })).toBeNull()
    expect(placeCallout({ box, art, dot: null, height })).toBeNull()
    expect(placeCallout({ box, art, dot: at(120, 300), height: 0 })).toBeNull()
  })

  it('never covers the drawing, wherever the dot is and whatever the drawing’s size', () => {
    for (let x0 = 0; x0 <= 200; x0 += 20) {
      for (let x1 = 250; x1 <= 448; x1 += 20) {
        for (let y = 0; y <= 690; y += 69) {
          for (let x = 0; x <= 448; x += 56) {
            const p = placeCallout({ box, art: { x0, y0: 0, x1, y1: 690 }, dot: at(x, y), height })
            if (!p) continue
            expect(clear(p, { x0, x1 }), `art ${x0}-${x1}, dot ${x},${y}`).toBe(true)
            expect(inside(p), `art ${x0}-${x1}, dot ${x},${y}`).toBe(true)
          }
        }
      }
    }
  })
})
