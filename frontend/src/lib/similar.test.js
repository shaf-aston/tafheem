import { describe, expect, it } from 'vitest'

import { placeLine, twinKeys, wordFlags } from './similar'

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
