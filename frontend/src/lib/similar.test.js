import { describe, expect, it } from 'vitest'

import { drillOf, fill, flagsOnPage, kindOf, nextUp, opening, pairId, placeLine, wordFlags, glossAt } from './similar'

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

describe('drillOf on twins that read the same', () => {
  const mine = { key: '27:3', text: 'ا ب ج', after: 'د ه و ز ح' }
  const partner = { key: '31:4', text: 'ا ب ج', after: 'ط ي ك ل م', changes: [] }

  it('asks what comes next, each verse against its twin, with the gap after the last word', () => {
    const questions = drillOf(mine, partner)
    expect(questions.map((q) => [q.key, q.right, q.wrong, q.next])).toEqual([
      ['27:3', 'د ه و ز', 'ط ي ك ل', true],
      ['31:4', 'ط ي ك ل', 'د ه و ز', true],
    ])
    expect(questions[0].span).toEqual([3, 3])
  })

  it('asks nothing when both run on the same way, or when a wording question exists', () => {
    expect(drillOf(mine, { ...partner, after: 'د ه و ز ح ط' })).toEqual([])
    const worded = drillOf({ ...mine, text: 'ا ب ج' }, { ...partner, text: 'ا ق ج', changes: [{ self: [1, 2], other: [1, 2] }] })
    expect(worded.every((q) => !q.next)).toBe(true)
  })

  it('says the surah ends when there is nothing after', () => {
    expect(opening('')).toBe('')
    expect(drillOf(mine, { ...partner, after: '' })[1].right).toBe('')
  })
})

describe('kindOf', () => {
  it('puts the benchmark types in plain words and leaves an unknown one blank', () => {
    expect(kindOf('replacement')).toBe('a different word')
    expect(kindOf('')).toBe('')
    expect(kindOf('something new')).toBe('')
  })
})

describe('nextUp', () => {
  const pairs = [{ id: 'a' }, { id: 'b' }, { id: 'c' }]
  const standing = (id) => ({ a: 'known', b: 'new', c: 'due' })[id]

  it('prefers what is due, then what is new', () => {
    expect(nextUp(pairs, standing)).toEqual({ id: 'c' })
    expect(nextUp(pairs, (id) => (id === 'c' ? 'known' : standing(id)))).toEqual({ id: 'b' })
  })

  it('looks on from the given pair and round again, and is null once all are known', () => {
    expect(nextUp(pairs, (id) => (id === 'c' ? 'new' : standing(id)), 1)).toEqual({ id: 'c' })
    expect(nextUp(pairs, (id) => (id === 'c' ? 'known' : standing(id)), 1)).toEqual({ id: 'b' })
    expect(nextUp(pairs, () => 'known')).toBeNull()
  })
})

describe('glossAt', () => {
  const grammar = [
    { arabic: 'ا', pos: 'N', meaning: 'Those who', grammar: ['noun'] },
    { arabic: 'ب', pos: 'V', meaning: 'believe', grammar: ['verb', 'present'] },
    { arabic: 'ج', pos: 'N', meaning: 'in the unseen', grammar: [] },
  ]
  it('reads the meaning and roles of the words in a span', () => {
    expect(glossAt(['ا', 'ب', 'ج'], grammar, [1, 3])).toEqual({
      meaning: 'believe in the unseen',
      roles: [{ arabic: 'ب', pos: 'V', grammar: ['verb', 'present'] }, { arabic: 'ج', pos: 'N', grammar: [] }],
    })
  })
  it('says nothing when the grammar does not line up with the text', () => {
    expect(glossAt(['ا', 'ب'], grammar, [0, 1])).toBeNull()
    expect(glossAt(['ا', 'ب', 'ج'], undefined, [0, 1])).toBeNull()
  })
})
