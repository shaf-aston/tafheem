import { describe, expect, it } from 'vitest'

import { byCategory, hardestWords, joinStats, overall, slowestWords } from './insights'

const word = (meaningKey, extra = {}) => ({
  ar: 'كلمة', en: 'word', meaningKey, wordType: 'noun', ...extra,
})
const stat = (item, extra = {}) => ({
  item, attempts: 1, wrong: 0, avgMs: null, inReview: false, ...extra,
})

describe('joining a record of answers to the words themselves', () => {
  it('puts each record beside its word', () => {
    const { rows } = joinStats([stat('train')], [word('train')])
    expect(rows[0].word.en).toBe('word')
  })

  it('keeps one row for words that share a meaning', () => {
    // Synonyms share a meaningKey, and the record is of the meaning, so two
    // spellings must not become two rows counting the same answers twice.
    const { rows } = joinStats([stat('train')], [word('train'), word('train', { ar: 'قطار' })])
    expect(rows).toHaveLength(1)
  })

  it('sets aside a record whose word has left the list rather than dropping it', () => {
    const { rows, orphans } = joinStats([stat('train'), stat('gone')], [word('train')])
    expect(rows).toHaveLength(1)
    expect(orphans.map((row) => row.item)).toEqual(['gone'])
  })

  it('answers nothing with nothing', () => {
    expect(joinStats([], [])).toEqual({ rows: [], orphans: [] })
  })
})

describe('what kind of word keeps going wrong', () => {
  const rows = [
    {
      ...stat('travel-a', { attempts: 10, wrong: 6 }),
      word: word('travel-a', { groups: ['everyday:travel'] }),
    },
    {
      ...stat('verb-a', { attempts: 10, wrong: 1 }),
      word: word('verb-a', { wordType: 'verb', groups: ['book:v-naqis'] }),
    },
  ]

  it('counts a tag as both the list it came from and the group inside it', () => {
    // "You miss everyday words" and "you miss hollow verbs" are different
    // findings, and one tag carries both.
    const keys = byCategory(rows).map((category) => category.key)
    expect(keys).toContain('everyday')
    expect(keys).toContain('everyday:travel')
  })

  it('counts the type of word too', () => {
    expect(byCategory(rows).map((category) => category.key)).toContain('noun')
  })

  it('puts the worst rate first', () => {
    const found = byCategory(rows)
    expect(found[0].rate).toBeCloseTo(0.6)
    expect(found.at(-1).rate).toBeCloseTo(0.1)
    // Every category the bad word belongs to outranks every category of the
    // good one; which of its own three leads is a tie and not worth pinning.
    expect(found.slice(0, 3).map((category) => category.key).sort())
      .toEqual(['everyday', 'everyday:travel', 'noun'])
  })

  it('says nothing about a category with too few answers behind it', () => {
    // Two wrong out of two is a Tuesday, not a weakness.
    const thin = [{
      ...stat('x', { attempts: 2, wrong: 2 }),
      word: word('x', { groups: ['everyday:travel'] }),
    }]
    expect(byCategory(thin, { minAttempts: 5 })).toEqual([])
    expect(byCategory(thin, { minAttempts: 2 })).not.toEqual([])
  })

  it('leaves out a category nothing has gone wrong in', () => {
    const perfect = [{
      ...stat('x', { attempts: 9, wrong: 0 }),
      word: word('x', { groups: ['everyday:travel'] }),
    }]
    expect(byCategory(perfect)).toEqual([])
  })

  it('uses the name the app already gives a group, and keeps the key when it has none', () => {
    const named = byCategory(rows, { labels: { everyday: 'Everyday speech' } })
    expect(named.find((category) => category.key === 'everyday').label).toBe('Everyday speech')
    expect(named.find((category) => category.key === 'noun').label).toBe('noun')
  })

  it('does not trip over a word with no groups at all', () => {
    const bare = [{ ...stat('x', { attempts: 6, wrong: 3 }), word: word('x') }]
    expect(byCategory(bare).map((category) => category.key)).toEqual(['noun'])
  })
})

describe('the words themselves', () => {
  const rows = [
    { ...stat('a', { attempts: 5, wrong: 4, avgMs: 9000 }), word: word('a') },
    { ...stat('b', { attempts: 5, wrong: 1, avgMs: null }), word: word('b') },
    { ...stat('c', { attempts: 5, wrong: 0, avgMs: 2000 }), word: word('c') },
  ]

  it('lists the ones got wrong most, worst first', () => {
    expect(hardestWords(rows).map((row) => row.item)).toEqual(['a', 'b'])
  })

  it('never lists a word that has always been right', () => {
    expect(hardestWords(rows).map((row) => row.item)).not.toContain('c')
  })

  it('ranks by time only where a time was honestly measured', () => {
    // avgMs is null when every answer for that word was slower than the cap;
    // treating that as zero would put a walked-away word top of the list.
    expect(slowestWords(rows).map((row) => row.item)).toEqual(['a', 'c'])
  })
})

describe('the line at the top', () => {
  it('counts answers, not words', () => {
    const rows = [
      { ...stat('a', { attempts: 8, wrong: 2, inReview: true }), word: word('a') },
      { ...stat('b', { attempts: 2, wrong: 0 }), word: word('b') },
    ]
    expect(overall(rows)).toMatchObject({ attempts: 10, wrong: 2, words: 2, inReview: 1 })
    expect(overall(rows).accuracy).toBeCloseTo(0.8)
  })

  it('has no accuracy to report before anything is answered', () => {
    expect(overall([]).accuracy).toBeNull()
  })

  // The nearest case the shut bar can meet: a word on record that has never
  // actually been asked. Zero of zero is not nought per cent right, and the bar
  // must show no figure at all rather than a "0%" nobody earned.
  it('has no accuracy for a word with a record but no attempts', () => {
    const rows = [{ ...stat('a', { attempts: 0, wrong: 0 }), word: word('a') }]
    expect(overall(rows).accuracy).toBeNull()
    expect(overall(rows).words).toBe(1)
  })
})
