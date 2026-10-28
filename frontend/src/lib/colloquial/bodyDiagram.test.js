import { describe, expect, it } from 'vitest'

import { hotspotsFor } from './bodyDiagram'

const word = (id, english) => ({ id, english, arabic: `ع-${id}`, transliteration: id, category: 'body' })

describe('hotspotsFor', () => {
  it('places a word it knows a position for, drops one it does not', () => {
    const spots = hotspotsFor([word('a', 'Knee'), word('b', 'unicorn')])
    expect(spots).toHaveLength(1)
    expect(spots[0].word.id).toBe('a')
    expect(spots[0]).toHaveProperty('x')
    expect(spots[0]).toHaveProperty('y')
  })

  it('matches case-insensitively and keeps the original word', () => {
    const [spot] = hotspotsFor([word('c', 'STOMACH')])
    expect(spot.word.english).toBe('STOMACH')
  })

  it('is empty with nothing to place', () => {
    expect(hotspotsFor([])).toEqual([])
  })
})
