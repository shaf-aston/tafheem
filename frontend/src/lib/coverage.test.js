import { describe, expect, it } from 'vitest'

import { coverageOf, learntLemmas, learntWords, surahShares } from './coverage'

// Four lemmas: 1,000 + 400 + 250 + 50 Qur'an words out of 10,000.
const coverage = { total: 10000, lemmas: ['قَالَ', 'كِتاب', 'رَبّ', 'نَبِيّ'], counts: [1000, 400, 250, 50] }
const word = (meaningKey, lemmas, ar = 'كلمة') => ({ ar, en: meaningKey, meaningKey, ...(lemmas && { lemmas }) })
// A learnt row from the progress summary; `words` are the ones answered right.
const known = (item, ...words) => ({ item, words })
const all = (...items) => items.map((item) => known(item))

describe('how much of the Qur\'an the known words cover', () => {
  it('credits only the smaller of two words sharing a meaning', () => {
    const words = [word('lord', [0]), word('lord', [2]), word('book', [1])]
    expect(coverageOf(words, coverage, all('lord'))).toBeCloseTo(0.025)
  })

  it('counts a lemma once when two known words share it', () => {
    const words = [word('book', [1]), word('scripture', [1, 3])]
    expect(coverageOf(words, coverage, all('book', 'scripture'))).toBeCloseTo(0.04)
  })

  it('is null when nothing is known', () => {
    expect(coverageOf([word('book', [1])], coverage, [])).toBeNull()
  })

  it('adds nothing for a known everyday word', () => {
    const words = [word('book', [1]), word('hello')]
    expect(coverageOf(words, coverage, all('book', 'hello'))).toBeCloseTo(0.04)
  })

  it('credits the very word that was asked, not the smaller one', () => {
    const words = [word('lord', [0], 'قال'), word('lord', [2], 'رب')]
    expect(coverageOf(words, coverage, [known('lord', 'قال')])).toBeCloseTo(0.1)
  })

  it('credits nothing for a meaning learnt only through an everyday word', () => {
    const words = [word('book', undefined, 'دفتر'), word('book', [1], 'كتاب')]
    expect(coverageOf(words, coverage, [known('book', 'دفتر')])).toBe(0)
  })

  it('falls back to the smaller word for answers saved without one', () => {
    const words = [word('lord', [0]), word('lord', [2])]
    expect(coverageOf(words, coverage, [known('lord')])).toBeCloseTo(0.025)
  })

  it('credits the Qur\'anic word when an everyday word shares its meaning', () => {
    const words = [word('book'), word('book', [1])]
    expect(coverageOf(words, coverage, all('book'))).toBeCloseTo(0.04)
  })
})

describe('how much of each surah the known words cover', () => {
  // Two surahs: 100 words using lemmas 0 and 1, then 50 words using lemmas 1 and 3.
  const bySurah = [{ total: 100, counts: { 0: 20, 1: 10 } }, { total: 50, counts: { 1: 5, 3: 10 } }]

  it('shares each surah by the same words the whole meter credits', () => {
    const words = [word('lord', [0]), word('lord', [2]), word('book', [1])]
    expect(surahShares(words, coverage, all('lord', 'book'), bySurah)).toEqual([0.1, 0.1])
  })

  it('is zero everywhere when nothing is known', () => {
    expect(surahShares([word('book', [1])], coverage, [], bySurah)).toEqual([0, 0])
  })
})

describe('which Qur\'an words the reader marks as learnt', () => {
  it('names the same lemmas the meter credits, as spelled in the corpus', () => {
    const words = [word('lord', [0]), word('lord', [2]), word('book', [1, 3])]
    expect(learntLemmas(words, coverage, all('lord', 'book'))).toEqual(new Set(['رَبّ', 'كِتاب', 'نَبِيّ']))
  })

  it('is empty when nothing is known', () => {
    expect(learntLemmas([word('book', [1])], coverage, []).size).toBe(0)
  })
})

describe('which printed words in an ayah are learnt', () => {
  it('marks a word learnt by any piece it is built from, as the meter counts it', () => {
    const ayah = [['ب', 'اسْم'], ['ي', 'ابْن', 'أُمّ'], ['قالَ']]
    expect(learntWords(ayah, new Set(['أُمّ', 'قالَ']))).toEqual([false, true, true])
  })

  it('is null when nothing in the ayah is learnt, so the plain text shows', () => {
    expect(learntWords([['قالَ']], new Set(['رَبّ']))).toBeNull()
    expect(learntWords(undefined, new Set(['رَبّ']))).toBeNull()
  })
})
