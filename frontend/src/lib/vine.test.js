import { describe, expect, it } from 'vitest'
import { snake, vinePath } from './vine'

const SIZE = { cell: 100, row: 120, top: 40, sway: 0, spread: 1.6 }

describe('the vine', () => {
  it('fills a row, then runs back along the next', () => {
    const { spots, height } = snake(5, 300, SIZE)
    expect(spots.map(({ x, r }) => [x, r])).toEqual([[50, 0], [150, 0], [250, 0], [250, 1], [150, 1]])
    expect(height).toBe(240)
  })

  it('spreads a short branch out but never further apart than spread cells', () => {
    expect(snake(2, 1000, SIZE).spots.map(({ x }) => x)).toEqual([80, 240])
  })

  it('keeps one to a row when the space is narrower than a cell', () => {
    expect(snake(2, 60, SIZE).spots.map(({ r }) => r)).toEqual([0, 1])
  })

  it('draws nothing for no steps and starts at the left edge when asked', () => {
    expect(vinePath([], 100)).toBe('')
    expect(vinePath(snake(1, 300, SIZE).spots, 100, true)).toMatch(/^M0 40/)
  })
})
