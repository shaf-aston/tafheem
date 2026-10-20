import { describe, expect, it } from 'vitest'

import { drillOf, fill, flagsOnPage, pairId, placeLine, wordFlags } from './similar'

describe('wordFlags', () => {
  it('flags the words inside a span, end exclusive', () => {
    expect(wordFlags(5, [[1, 3]])).toEqual([false, true, true, false, false])
  })

  it('flags nothing for an empty diff', () => {
    expect(wordFlags(3, [])).toEqual([false, false, false])
    expect(wordFlags(3)).toEqual([false, false, false])
  })

  it('merges overlapping and duplicate spans, and clamps to the verse', () => {
    expect(wordFlags(4, [[0, 2], [1, 3], [1, 3], [3, 99]])).toEqual([true, true, true, true])
  })
})

describe('flagsOnPage', () => {
  it('skips stand-alone pause marks so later spans stay on their word', () => {
    expect(flagsOnPage(['ب', 'ج', 'د'], 'ب ۚ ج د', [[2, 4]])).toEqual([false, true, true])
  })

  it('matches a word the page writes whole to the two the backend splits', () => {
    // يَٰمُوسَىٰ (one) against يَا مُوسَىٰ (two), flagged on the second
    expect(flagsOnPage(['قال', 'يَٰمُوسَىٰ', 'اذهب'], 'قال يَا مُوسَىٰ اذهب', [[2, 3]])).toEqual([false, true, false])
  })
})

describe('placeLine', () => {
  it('names two surahs', () => {
    expect(placeLine('2:59', '7:162')).toBe("This one is in Surah Al-Baqarah, that one in Surah Al-A'raf")
  })

  it('says so when both are in one surah', () => {
    expect(placeLine('2:59', '2:60')).toContain('Both are in Surah Al-Baqarah')
  })
})

describe('drillOf', () => {
  const mine = { key: '2:59', text: 'فبدل الذين ظلموا قولا فأنزلنا' }
  const partner = {
    key: '7:162',
    text: 'فبدل الذين ظلموا منهم قولا فأرسلنا',
    changes: [{ self: [3, 3], other: [3, 4] }, { self: [4, 5], other: [5, 6] }],
  }

  it('asks every difference, from both verses', () => {
    const qs = drillOf(mine, partner)
    expect(qs.map((q) => [q.key, q.right, q.wrong])).toEqual([
      ['2:59', '', 'منهم'],
      ['2:59', 'فأنزلنا', 'فأرسلنا'],
      ['7:162', 'منهم', ''],
      ['7:162', 'فأرسلنا', 'فأنزلنا'],
    ])
  })

  it('leaves out a difference longer than the limit on either side', () => {
    expect(drillOf(mine, partner, 0)).toEqual([])
    expect(drillOf(mine, { ...partner, changes: [{ self: [0, 5], other: [0, 1] }] }, 2)).toEqual([])
  })

  it('has nothing to ask of a partner without paired changes', () => {
    expect(drillOf(mine, { ...partner, changes: undefined })).toEqual([])
  })
})

describe('pairId', () => {
  it('is the same whichever verse is asked', () => {
    expect(pairId('7:162', '2:59')).toBe('2:59~7:162')
    expect(pairId('2:59', '7:162')).toBe('2:59~7:162')
    expect(pairId('10:1', '9:2')).toBe('9:2~10:1')
  })
})

describe('fill', () => {
  it('puts named values into the copy', () => {
    expect(fill('Question {n} of {of}', { n: 2, of: 5 })).toBe('Question 2 of 5')
  })
})
