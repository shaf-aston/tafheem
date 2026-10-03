import { describe, expect, it } from 'vitest'

import { closestSpans, flagsOnPage, placeLine, twinKeys, wordFlags } from './similar'

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

describe('closestSpans', () => {
  const text = 'ا ب ج د هـ و ز ح ط ي'
  const far = { diff_self: [[0, 8]] }
  const near = { diff_self: [[1, 2]] }

  it('picks the partner with the fewest differing words', () => {
    expect(closestSpans(text, [far, { diff_self: [[1, 4]] }, near])).toEqual([[1, 2]])
  })

  it('keeps API order on a tie', () => {
    const first = { diff_self: [[0, 1]] }
    expect(closestSpans(text, [first, { diff_self: [[5, 6]] }])).toBe(first.diff_self)
  })

  it('covers nothing when every twin differs in more than half the verse', () => {
    expect(closestSpans(text, [far, { diff_self: [[0, 6]] }])).toEqual([])
    expect(closestSpans(text, [])).toEqual([])
  })

  it('counts exactly half as near', () => {
    expect(closestSpans(text, [{ diff_self: [[0, 5]] }])).toEqual([[0, 5]])
  })
})

describe('twinKeys', () => {
  it('collects keys across groups, once each', () => {
    expect([...twinKeys([{ keys: ['2:59', '7:162'] }, { keys: ['7:162', '3:1'] }])]).toHaveLength(3)
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
