import { describe, expect, it } from 'vitest'

import data from '../../public/grow/basics.json'
import { makeRandom } from './quiz'
import {
  FORMS, INTRO, MODULE, SUN_LETTERS, article, definite, english, isSun, keyOfBasic, plain,
  teachWord, toArabicCard, toEnglishCard, wordAsks, wrongForms,
} from './alifLam'

const nfc = (text) => text.normalize('NFC')
const letters = (text) => text.replace(/[ً-ْٰ\s]/g, '')
// A generator that hands back the given numbers, in turn, again and again.
const fixed = (...values) => { let i = 0; return () => values[i++ % values.length] }

const book = { id: 'book', ar: 'كِتَاب', en: 'book' }
const sun = { id: 'sun', ar: 'شَمْس', en: 'sun' }
const apple = { id: 'apple', ar: 'تُفَّاحَة', en: 'apple' }
const hour = { id: 'hour', ar: 'سَاعَة', en: 'hour', a: 'an' }

describe('sun and moon letters', () => {
  const ALL = [...'ابتثجحخدذرزسشصضطظعغفقكلمنهوي']
  it('are fourteen and fourteen', () => {
    expect(SUN_LETTERS.size).toBe(14)
    expect(ALL.filter((letter) => SUN_LETTERS.has(letter))).toHaveLength(14)
  })
  it('reads the first letter past its vowel', () => {
    expect(isSun('شَمْس')).toBe(true)
    expect(isSun('قَمَر')).toBe(false)
    expect(isSun('أَب')).toBe(false)
    expect(isSun('نَجْم')).toBe(true)
    expect(isSun('لَيْل')).toBe(true)
  })
})

describe('plain', () => {
  it('takes tanween off, with the alif fathatan sits on', () => {
    expect(plain('كِتَابٌ')).toBe(nfc('كِتَاب'))
    expect(plain('كِتَابٍ')).toBe(nfc('كِتَاب'))
    expect(plain('كِتَابًا')).toBe(nfc('كِتَاب'))
    expect(plain(' كِتَاب ')).toBe(nfc('كِتَاب'))
  })
  it('leaves a word without tanween as it is, its own final alif too', () => {
    expect(plain('كِتَاب')).toBe(nfc('كِتَاب'))
    expect(plain('عَصَا')).toBe(nfc('عَصَا'))
  })
})

describe('definite', () => {
  it('keeps the ل, with a sukun, before a moon letter', () => {
    expect(definite('كِتَاب')).toBe(nfc('الْكِتَاب'))
    expect(definite('أَب')).toBe(nfc('الْأَب'))
    expect(definite('قَمَر')).toBe(nfc('الْقَمَر'))
  })
  it('doubles a sun letter with shadda, the ل unvowelled', () => {
    expect(definite('شَمْس')).toBe(nfc('الشَّمْس'))
    expect(definite('لَيْل')).toBe(nfc('اللَّيْل'))
    expect(definite('تُفَّاحَة')).toBe(nfc('التُّفَّاحَة'))
  })
  it('drops tanween first: ال and tanween never meet', () => {
    expect(definite('كِتَابٌ')).toBe(nfc('الْكِتَاب'))
    expect(definite('شَمْسٌ')).toBe(nfc('الشَّمْس'))
  })
})

describe('the wrong forms', () => {
  it('bare: no ال', () => expect(FORMS.bare('كِتَابٌ')).toBe(nfc('كِتَاب')))
  it('tanween: ال and tanween together', () => {
    expect(FORMS.tanween('كِتَاب')).toBe(nfc('الْكِتَابٌ'))
    expect(FORMS.tanween('شَمْس')).toBe(nfc('الشَّمْسٌ'))
  })
  it('tanween keeps a doubled last letter doubled', () => {
    expect(FORMS.tanween('أُمّ')).toBe(nfc('الْأُمٌّ'))
    expect(FORMS.tanween('تَلّ')).toBe(nfc('التَّلٌّ'))
  })
  it('apart: ال as a word on its own', () => expect(FORMS.apart('كِتَابٌ')).toBe(`ال ${nfc('كِتَاب')}`))
  it('heard: a sun word spelt as said, the ل gone', () => {
    expect(FORMS.heard('شَمْس')).toBe(nfc('اشَّمْس'))
    expect(FORMS.heard('تَلّ')).toBe(nfc('اتَّلّ'))
  })
  it("heard: nothing for a ل word, since الَّيْل is the Qur'an's own spelling", () => expect(FORMS.heard('لَيْل')).toBeNull())
  it('heard: nothing for a moon word, whose ل is said', () => expect(FORMS.heard('كِتَاب')).toBeNull())

  it('asks the bare word and the sun spelling for a sun word', () => {
    expect(wrongForms('شَمْس', fixed(0.1))).toEqual(['bare', 'heard'])
    expect(wrongForms('شَمْس', fixed(0.9))).toEqual(['bare', 'heard'])
  })
  it('asks the bare word and tanween or apart for a moon word', () => {
    expect(wrongForms('كِتَاب', fixed(0.49))).toEqual(['bare', 'tanween'])
    expect(wrongForms('كِتَاب', fixed(0.5))).toEqual(['bare', 'apart'])
  })
  it('asks a ل word like a moon word', () => {
    expect(wrongForms('لَيْل', fixed(0.49))).toEqual(['bare', 'tanween'])
    expect(wrongForms('لَيْل', fixed(0.5))).toEqual(['bare', 'apart'])
  })
})

describe('english', () => {
  it('says a or an by the first letter, unless the word says otherwise', () => {
    expect(article(book)).toBe('a')
    expect(article(apple)).toBe('an')
    expect(article({ en: 'Egg' })).toBe('an')
    expect(article(hour)).toBe('an')
    expect(article({ en: 'uniform', a: 'a' })).toBe('a')
  })
  it('the or a, then the word', () => {
    expect(english(book, true)).toBe('the book')
    expect(english(book, false)).toBe('a book')
    expect(english(apple, false)).toBe('an apple')
  })
  it('files every answer under the word’s id', () => expect(keyOfBasic(book)).toBe('book'))
})

describe('toArabicCard', () => {
  it('asks for “the book” among the word’s own wrong forms', () => {
    const card = toArabicCard(book, true, fixed(0.2))
    expect(card).toMatchObject({ kind: 'choose', id: 'the:book', tag: 'New word', ask: 'Which one is “the book”?', arabic: true, answer: 'right' })
    const texts = Object.fromEntries(card.options.map((option) => [option.id, option.text]))
    expect(texts).toEqual({ right: nfc('الْكِتَاب'), bare: nfc('كِتَاب'), tanween: nfc('الْكِتَابٌ') })
    expect(card.record).toEqual({ module: MODULE, item: 'book', context: { world: 'basics', direction: 'to-arabic', word: nfc('كِتَاب') } })
    expect(card.why).toBe(`${nfc('الْكِتَاب')} = the book. ال is joined to the front of the word, and a word with ال never ends in -un (ٌ).`)
  })
  it('says why a sun word’s ل is written though not said', () => {
    const card = toArabicCard(sun, false, fixed(0.7))
    expect(card.tag).toBe('Review')
    expect(card.options.map((option) => option.id).sort()).toEqual(['bare', 'heard', 'right'])
    expect(card.why).toBe(`${nfc('الشَّمْس')} = the sun. The ل of ال is written, but not said: it joins the ش after it.`)
  })
  it('shuffles the options by the random it is given', () => {
    const orders = new Set(Array.from({ length: 12 }, (_, seed) => toArabicCard(book, true, makeRandom(seed + 1)).options.map((o) => o.id).join()))
    expect(orders.size).toBeGreaterThan(1)
  })
})

describe('toEnglishCard', () => {
  it('shows the word with ال: the answer is “the …”', () => {
    const card = toEnglishCard(book, true, fixed(0.49, 0.9))
    expect(card).toMatchObject({ kind: 'choose', id: 'means:book', ask: 'What does it mean?', ar: nfc('الْكِتَاب'), answer: 'the' })
    expect(card.arabic).toBeUndefined()
    expect(card.options).toEqual(expect.arrayContaining([{ id: 'the', text: 'the book' }, { id: 'a', text: 'a book' }]))
    expect(card.options).toHaveLength(2)
    expect(card.why).toBe(`ال at the start means “the”: ${nfc('الْكِتَاب')} = the book.`)
    expect(card.record.context.direction).toBe('to-english')
  })
  it('shows the word without ال: the answer is “a …” or “an …”', () => {
    const card = toEnglishCard(apple, false, fixed(0.5, 0.1))
    expect(card).toMatchObject({ ar: nfc('تُفَّاحَة'), answer: 'a', tag: 'Review' })
    expect(card.options.find((option) => option.id === 'a').text).toBe('an apple')
    expect(card.why).toBe(`No ال at the start, so it is “an apple”. Add ال and it is “the apple”: ${nfc('التُّفَّاحَة')}.`)
  })
})

describe('teachWord and wordAsks', () => {
  it('teach a new word with ال and without it, then ask it both ways', () => {
    expect(teachWord(book)).toEqual({ kind: 'teach', id: 'teach:book', tag: 'New word', ar: nfc('الْكِتَاب'), en: 'the book', also: { ar: nfc('كِتَاب'), en: 'a book' } })
    expect(wordAsks(book, false, makeRandom(2)).map((card) => [card.id, card.tag])).toEqual([['the:book', 'Review'], ['means:book', 'Review']])
  })
  it('the intro shows ال and a word that has it', () => {
    expect(INTRO).toEqual({ kind: 'teach', id: 'teach:al', tag: 'New', ar: 'ال', en: 'means “the”', also: { ar: definite('كِتَاب'), en: 'the book' } })
  })
})

describe('every word in the list', () => {
  const WORDS = data.words

  it('gives one right answer, unique options, every wrong one built from the word itself', () => {
    for (const word of WORDS) {
      for (let seed = 1; seed <= 4; seed += 1) {
        const card = toArabicCard(word, true, makeRandom(seed))
        const texts = card.options.map((option) => option.text)
        expect(new Set(texts).size, word.id).toBe(3)
        expect(card.options.filter((option) => option.id === card.answer), word.id).toHaveLength(1)
        expect(texts.filter((text) => text === definite(word.ar)), word.id).toHaveLength(1)
        const core = letters(plain(word.ar))
        for (const text of texts) expect(letters(text), word.id).toContain(core)
      }
    }
  })

  it('writes its tanween form as the right answer with only tanween added', () => {
    for (const word of WORDS) expect(FORMS.tanween(word.ar).replace('\u064C', ''), word.id).toBe(definite(word.ar))
  })

  it('is written as the cards need it: bare, vowelled, no ال, ids unique', () => {
    expect(new Set(WORDS.map(keyOfBasic)).size).toBe(WORDS.length)
    for (const word of WORDS) {
      expect(plain(word.ar), word.id).toBe(word.ar.normalize('NFC'))
      expect(word.ar.startsWith('ال'), word.id).toBe(false)
      // One word, starting on a letter with its mark; never a bare alif (hamzat al-wasl, اِسْم), which ال changes.
      expect(word.ar, word.id).toMatch(/^[\u0621-\u0626\u0628-\u064A][\u064E-\u0652]\S*$/)
      // Pausal: no vowel on the last letter (a shadda may stay), so tanween can go straight on.
      expect(word.ar, word.id).toMatch(/[\u0621-\u064A]\u0651?$/)
      expect(word.en, word.id).toMatch(/^[a-z]+$/)
    }
  })

})
