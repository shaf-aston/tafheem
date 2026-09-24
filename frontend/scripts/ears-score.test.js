import { describe, expect, it } from 'vitest'

import { score } from './ears-score'

describe('score', () => {
  it('marks a matching reading clean', () => {
    const page = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
    const s = score(page, page)
    expect(s).toEqual({ words: 4, wrong: 0, check: 0, missed: 0, extra: 0, quiet: 0 })
  })

  it('counts a reading with none of the page in it as fully missed, not perfect', () => {
    const page = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
    const s = score(page, 'completely unrelated words said instead')
    expect(s.quiet).toBe(1)
    expect(s.missed).toBe(4)
    expect(s.words).toBe(4)
  })

  it('does not count a pause mark between two words as a word', () => {
    // 2:127 as backend/data/quran/imlaei.json stores it: the small sad sits
    // alone between minna and innaka.
    const page = 'رَبَّنَا تَقَبَّلْ مِنَّا ۖ إِنَّكَ أَنتَ'
    const s = score(page, 'رَبَّنَا تَقَبَّلْ مِنَّا إِنَّكَ أَنْتَ')
    expect(s.words).toBe(5)
    expect(s.missed).toBe(0)
  })
})
