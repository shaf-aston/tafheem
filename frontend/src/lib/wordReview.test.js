import { describe, expect, it } from 'vitest'

import { wordKey } from './wordDrills'
import { reviewOf, SESSION } from './wordReview'

const w = (arabic) => ({ arabic, english: arabic, transliteration: arabic })
const words = [w('a'), w('b'), w('c'), w('d')]
const row = (word, due, dueAt) => ({ item: wordKey('fusha', word), due, dueAt })

describe('reviewOf', () => {
  it('asks the due words first, longest waiting first, then the new ones', () => {
    const rows = [row(words[0], false, '2026-12-01'), row(words[1], true, '2026-10-05'), row(words[3], true, '2026-10-01')]
    const r = reviewOf(words, rows, 'fusha')
    expect(r.session.map((x) => x.arabic)).toEqual(['d', 'b', 'c'])
    expect([r.due, r.fresh, r.later, r.next]).toEqual([2, 1, 1, '2026-12-01'])
  })

  it('treats a word as the same word only in the same dialect', () => {
    expect(reviewOf(words, [row(words[0], false, 'x')], 'egyptian').fresh).toBe(4)
  })

  it('keeps a session short', () => {
    const many = Array.from({ length: 30 }, (_, i) => w(String(i)))
    expect(reviewOf(many, [], 'fusha').session).toHaveLength(SESSION)
  })
})
