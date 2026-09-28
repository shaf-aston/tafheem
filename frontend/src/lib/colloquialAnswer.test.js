import { describe, expect, it } from 'vitest'
import { bankOf, hasAnswer, isRight, judge } from './colloquialAnswer'

const accepted = ['كيفك؟', 'keefak']

describe('isRight', () => {
  it('accepts the answer, a vowel-marked spelling and the transliteration', () => {
    expect(isRight('كيفك؟', accepted)).toBe(true)
    expect(isRight('كَيفَك', accepted)).toBe(true)
    expect(isRight('Keefak?', accepted)).toBe(true)
  })
  it('never marks a blank or a wrong answer right', () => {
    expect(isRight('', accepted)).toBe(false)
    expect(isRight('   ', accepted)).toBe(false)
    expect(isRight('shukran', accepted)).toBe(false)
  })
})

describe('judge', () => {
  it('a picked option must match exactly', () => {
    expect(judge({ type: 'choose', answer: 'مرحبا' }, 'مرحبا')).toBe(true)
    expect(judge({ type: 'choose', answer: 'مرحبا' }, 'مرحبًا')).toBe(false)
  })
  it('an arranged sentence is its words joined', () => {
    const ex = { type: 'reorder', accepted: ['شو اسمك'] }
    expect(judge(ex, ['شو', 'اسمك'])).toBe(true)
    expect(judge(ex, ['اسمك', 'شو'])).toBe(false)
  })
})

describe('bankOf and hasAnswer', () => {
  it('keeps a repeated word twice, prefers the authored words', () => {
    expect(bankOf({ answer: 'لا لا شكرا' })).toEqual(['لا', 'لا', 'شكرا'])
    expect(bankOf({ answer: 'x y', words: ['y', 'x', 'z'] })).toEqual(['y', 'x', 'z'])
  })
  it('empty box and empty sentence are not answers', () => {
    expect(hasAnswer('')).toBe(false)
    expect(hasAnswer([])).toBe(false)
    expect(hasAnswer(['a'])).toBe(true)
  })
})
