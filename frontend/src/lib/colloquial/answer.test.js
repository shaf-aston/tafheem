import { describe, expect, it } from 'vitest'
import { bankOf, hasAnswer, isRight, takesLatin, ARRANGED, PICKED, TYPED } from './answer'

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

describe('isRight, a transliteration as it sounds', () => {
  it('meets the spellings a learner without an Arabic keyboard writes', () => {
    const peace = ['وَعَلَيْكُم السَّلَامُ', 'wa 3aleikum es-salaam']
    for (const said of ['wa alaykum el salam', 'wa 3alaykum issalaam', 'Wa aleikum is-salam']) expect(isRight(said, peace), said).toBe(true)
    expect(isRight('ana min el qahira', ['أنا من القاهرة', 'ana men el-2aahira'])).toBe(true)
    expect(isRight('itsharrafna', ['اِتْشَرَّفْنَا', 'etsharrafna'])).toBe(true)
  })

  it('still tells the man from the woman, and a wrong sentence from a right one', () => {
    expect(isRight('ismik eh', ['اِسْمَك إِيه؟', 'ismak eh?'])).toBe(false)
    expect(isRight('keefik alyoom', ['كيفَك اليوم؟', 'keefak alyoom?'])).toBe(false)
    expect(isRight('ana min dimashq', ['أنا من القاهرة', 'ana men el-2aahira'])).toBe(false)
    expect(isRight('', ['bas'])).toBe(false)
  })
})

describe('isRight, Arabic written either way', () => {
  it('takes ه for ة and ي for ى', () => {
    expect(isRight('انا من القاهره', ['أنا من القاهرة'])).toBe(true)
    expect(isRight('كويسه', ['كويسة'])).toBe(true)
    expect(isRight('علي', ['على'])).toBe(true)
    expect(isRight('كويس', ['كويسة'])).toBe(false)
  })
})

describe('TYPED.unfit', () => {
  it('asks for Arabic when Latin letters meet an answer with no Latin spelling', () => {
    expect(TYPED.unfit({ accepted: ['كويسة'] }, 'kwayyisa')).toBe(true)
    expect(TYPED.unfit({ accepted: ['كويسة', 'kwayyisa'] }, 'kwayyisa')).toBe(false)
    expect(TYPED.unfit({ accepted: ['كويسة'] }, 'كويسة')).toBe(false)
    expect(takesLatin(['اسمي', 'ismi'])).toBe(true)
  })
})
