import { describe, expect, it } from 'vitest'

import { savedEntry, savedToAsk, seenAt, tableWordFor } from './savedWords'

const COVERAGE = { lemmas: ['كِتَاب', 'أَوَّل', 'مِن'] }
const WORDS = [
  { ar: 'كِتَاب', en: 'book', meaningKey: 'book', lemmas: [0] },
  { ar: 'أَوَّل', en: 'first', meaningKey: 'first', lemmas: [1] },
]

describe('saved words', () => {
  it('finds the table word by lemma, and none for a lemma the lists leave out', () => {
    expect(tableWordFor('أَوَّل', WORDS, COVERAGE).meaningKey).toBe('first')
    expect(tableWordFor('مِن', WORDS, COVERAGE)).toBeNull()
    expect(tableWordFor(undefined, WORDS, COVERAGE)).toBeNull()
  })

  it('keeps where a corpus word was seen, and nothing for a word from elsewhere', () => {
    expect(seenAt({ position: '2:255:3' })).toBe('2:255')
    expect(seenAt({ position: '3' })).toBeNull()
    const word = { lemma: 'أَوَّل', root: 'أول', position: '57:3:1' }
    expect(savedEntry(word, WORDS[1])).toEqual({ key: 'first', lemma: 'أَوَّل' })
  })

  it('asks a saved word until the store calls it known, never twice beside what is due', () => {
    const saved = [{ key: 'first' }, { key: 'book' }, { key: 'first' }, { key: 'old' }]
    const summary = [{ item: 'book', known: true }, { item: 'old', known: false }]
    expect(savedToAsk(saved, summary, [])).toEqual(['first', 'old'])
    expect(savedToAsk(saved, summary, ['old'])).toEqual(['first'])
  })
})
