import { describe, expect, it } from 'vitest'
import { bankOf, hasAnswer, isRight, ARRANGED, PICKED, TYPED } from './colloquialAnswer'

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

describe('how an answer is judged', () => {
  it('a typed answer goes through isRight', () => {
    expect(TYPED.judge({ accepted }, 'Keefak?')).toBe(true)
    expect(TYPED.judge({ accepted }, 'هلا')).toBe(false)
  })
  it('a picked option must match exactly', () => {
    expect(PICKED.judge({ answer: 'مرحبا' }, 'مرحبا')).toBe(true)
    expect(PICKED.judge({ answer: 'مرحبا' }, 'مرحبًا')).toBe(false)
  })
  it('an arranged sentence is its words joined', () => {
    const ex = { accepted: ['شو اسمك'] }
    expect(ARRANGED.judge(ex, ['شو', 'اسمك'])).toBe(true)
    expect(ARRANGED.judge(ex, ['اسمك', 'شو'])).toBe(false)
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
