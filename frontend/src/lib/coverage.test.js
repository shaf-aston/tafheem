import { describe, expect, it } from 'vitest'

import { coverageOf, surahShares } from './coverage'

// Four lemmas: 1,000 + 400 + 250 + 50 Qur'an words out of 10,000.
const coverage = { total: 10000, lemmas: ['قَالَ', 'كِتاب', 'رَبّ', 'نَبِيّ'], counts: [1000, 400, 250, 50] }
const word = (meaningKey, lemmas) => ({ ar: 'كلمة', en: meaningKey, meaningKey, ...(lemmas && { lemmas }) })

describe('how much of the Qur\'an the known words cover', () => {
  it('credits only the smaller of two words sharing a meaning', () => {
    const words = [word('lord', [0]), word('lord', [2]), word('book', [1])]
    expect(coverageOf(words, coverage, ['lord'])).toBeCloseTo(0.025)
  })

  it('counts a lemma once when two known words share it', () => {
    const words = [word('book', [1]), word('scripture', [1, 3])]
    expect(coverageOf(words, coverage, ['book', 'scripture'])).toBeCloseTo(0.04)
  })

  it('is null when nothing is known', () => {
    expect(coverageOf([word('book', [1])], coverage, [])).toBeNull()
  })

  it('adds nothing for a known everyday word', () => {
    const words = [word('book', [1]), word('hello')]
    expect(coverageOf(words, coverage, ['book', 'hello'])).toBeCloseTo(0.04)
  })

  it('credits the Qur\'anic word when an everyday word shares its meaning', () => {
    const words = [word('book'), word('book', [1])]
    expect(coverageOf(words, coverage, ['book'])).toBeCloseTo(0.04)
  })
})

describe('how much of each surah the known words cover', () => {
  // Two surahs: 100 words using lemmas 0 and 1, then 50 words using lemmas 1 and 3.
  const bySurah = [{ total: 100, counts: { 0: 20, 1: 10 } }, { total: 50, counts: { 1: 5, 3: 10 } }]

  it('shares each surah by the same words the whole meter credits', () => {
    const words = [word('lord', [0]), word('lord', [2]), word('book', [1])]
    expect(surahShares(words, coverage, ['lord', 'book'], bySurah)).toEqual([0.1, 0.1])
  })

  it('is zero everywhere when nothing is known', () => {
    expect(surahShares([word('book', [1])], coverage, [], bySurah)).toEqual([0, 0])
  })
})
