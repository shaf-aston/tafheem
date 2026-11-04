import { describe, expect, it } from 'vitest'

import basics from '../../../public/grow/basics.json'
import { dualTable, isFeminine, joinedTable, ofTable, peopleTable, pointingTable, pronounTable } from './nounForms'

const nfc = (text) => text.normalize('NFC')
const at = (entries, key) => entries.find((entry) => entry.key === key)
const book = { id: 'book', ar: 'كِتَاب', en: 'book' }

describe('peopleTable', () => {
  const say = (entries) => entries.map((entry) => [entry.key, entry.ar, entry.en])
  it('makes a man, a woman, men and women with ة, ـُونَ and ـَات', () => {
    expect(say(peopleTable({ ar: 'مُسْلِم', en: 'Muslim', many: 'Muslims' }))).toEqual([
      ['man', nfc('مُسْلِم'), 'a Muslim (man)'], ['woman', nfc('مُسْلِمَة'), 'a Muslim (woman)'],
      ['men', nfc('مُسْلِمُونَ'), 'Muslims (men)'], ['women', nfc('مُسْلِمَات'), 'Muslims (women)'],
    ])
  })
  it('says “an” where the English starts with a vowel', () => {
    expect(at(peopleTable({ ar: 'مُهَنْدِس', en: 'engineer', many: 'engineers' }), 'woman').en).toBe('an engineer (woman)')
  })
  it('spells every person’s four forms apart, and each says one thing', () => {
    for (const person of basics.people) {
      const entries = peopleTable(person)
      expect(new Set(entries.map((entry) => entry.ar)).size, person.id).toBe(4)
      expect(new Set(entries.map((entry) => entry.en)).size, person.id).toBe(4)
    }
  })
})

describe('joinedTable', () => {
  const pen = { id: 'pen', ar: 'قَلَم', en: 'pen' }
  const candle = { id: 'candle', ar: 'شَمْعَة', en: 'candle' }
  it('joins وَ, بِـ and كَـ to the word with ال, and لِـ in place of its ا', () => {
    expect(at(joinedTable(pen), 'and')).toMatchObject({ ar: nfc('وَالْقَلَم'), en: 'and the pen' })
    expect(at(joinedTable(pen), 'with')).toMatchObject({ ar: nfc('بِالْقَلَم'), en: 'with the pen' })
    expect(at(joinedTable(pen), 'for')).toMatchObject({ ar: nfc('لِلْقَلَم'), en: 'for the pen' })
    expect(at(joinedTable(pen), 'like')).toMatchObject({ ar: nfc('كَالْقَلَم'), en: 'like the pen' })
    expect(at(joinedTable(candle), 'for').ar).toBe(nfc('لِلشَّمْعَة'))
  })
  it('misspells them as a beginner does: apart, or keeping the ا, with no meaning', () => {
    expect(at(joinedTable(pen), 'wrong:apart:and')).toEqual({ key: 'wrong:apart:and', ar: nfc('وَ الْقَلَم'), en: null })
    expect(at(joinedTable(pen), 'wrong:alif:for').ar).toBe(nfc('لِالْقَلَم'))
    expect(at(joinedTable(pen), 'wrong:alif:with')).toBeUndefined()
  })
})

describe('pointingTable', () => {
  const car = { id: 'car', ar: 'سَيَّارَة', en: 'car' }
  it('says “this is a …” without ال and “this …” with it, for this and that', () => {
    const entries = pointingTable(book)
    expect(at(entries, 'this-is')).toMatchObject({ ar: nfc('هٰذَا كِتَاب'), en: 'this is a book' })
    expect(at(entries, 'this')).toMatchObject({ ar: nfc('هٰذَا الْكِتَاب'), en: 'this book' })
    expect(at(entries, 'that-is')).toMatchObject({ ar: nfc('ذٰلِكَ كِتَاب'), en: 'that is a book' })
    expect(at(entries, 'that')).toMatchObject({ ar: nfc('ذٰلِكَ الْكِتَاب'), en: 'that book' })
  })
  it('takes هٰذِهِ and تِلْكَ for a word with ة, and gives the other gender no meaning', () => {
    expect(isFeminine(car)).toBe(true)
    expect(isFeminine(book)).toBe(false)
    expect(at(pointingTable(car), 'this-is').ar).toBe(nfc('هٰذِهِ سَيَّارَة'))
    expect(at(pointingTable(car), 'that').ar).toBe(nfc('تِلْكَ السَّيَّارَة'))
    expect(at(pointingTable(car), 'wrong:gender:this-is')).toEqual({ key: 'wrong:gender:this-is', ar: nfc('هٰذَا سَيَّارَة'), en: null })
    expect(at(pointingTable(book), 'wrong:gender:that').ar).toBe(nfc('تِلْكَ الْكِتَاب'))
  })
})

describe('pronounTable', () => {
  const muslim = { ar: 'مُسْلِم', en: 'Muslim', many: 'Muslims' }
  const say = (key) => [at(pronounTable(muslim), key).ar, at(pronounTable(muslim), key).en]
  it('sets each pronoun before the person in the form that agrees with it, with no word for “is”', () => {
    expect(say('he')).toEqual([nfc('هُوَ مُسْلِم'), 'he is a Muslim'])
    expect(say('she')).toEqual([nfc('هِيَ مُسْلِمَة'), 'she is a Muslim'])
    expect(say('they')).toEqual([nfc('هُمْ مُسْلِمُونَ'), 'they are Muslims'])
    expect(say('I')).toEqual([nfc('أَنَا مُسْلِم'), 'I am a Muslim (a man speaking)'])
    expect(say('I-woman')).toEqual([nfc('أَنَا مُسْلِمَة'), 'I am a Muslim (a woman speaking)'])
    expect(say('we')).toEqual([nfc('نَحْنُ مُسْلِمُونَ'), 'we are Muslims'])
    expect(say('you-woman')).toEqual([nfc('أَنْتِ مُسْلِمَة'), 'you are a Muslim (one woman)'])
    expect(say('you-all')).toEqual([nfc('أَنْتُمْ مُسْلِمُونَ'), 'you are Muslims (all of you)'])
  })
  it('gives a pronoun that does not agree no meaning', () => {
    expect(at(pronounTable(muslim), 'wrong:agree:she')).toEqual({ key: 'wrong:agree:she', ar: nfc('هِيَ مُسْلِم'), en: null })
    expect(at(pronounTable(muslim), 'wrong:agree:they').ar).toBe(nfc('هُمْ مُسْلِم'))
  })
  it('says “an” before a vowel, and every person’s forms are spelt and said apart', () => {
    expect(at(pronounTable({ ar: 'مُهَنْدِس', en: 'engineer', many: 'engineers' }), 'he').en).toBe('he is an engineer')
    for (const person of basics.people) {
      const entries = pronounTable(person)
      expect(new Set(entries.map((entry) => entry.ar)).size, person.id).toBe(entries.length)
      expect(new Set(entries.filter((entry) => entry.en).map((entry) => entry.en)).size, person.id).toBe(9)
    }
  })
})

describe('ofTable', () => {
  const teacher = { id: 'teacher', ar: 'مُعَلِّم', en: 'teacher' }
  const student = { id: 'student', ar: 'طَالِب', en: 'student' }
  const car = { id: 'car', ar: 'سَيَّارَة', en: 'car' }
  const table = ofTable({ thing: book, owner: teacher })
  it('says “the … of …” with ال on the second word only', () => {
    expect(at(table, 'of')).toMatchObject({ ar: nfc('كِتَاب الْمُعَلِّم'), en: 'the teacher’s book' })
    expect(at(table, 'a')).toMatchObject({ ar: nfc('كِتَاب مُعَلِّم'), en: 'a teacher’s book' })
    expect(at(table, 'turned')).toMatchObject({ ar: nfc('مُعَلِّم الْكِتَاب'), en: 'the book’s teacher' })
    expect(at(table, 'is')).toMatchObject({ ar: nfc('الْكِتَاب لِلْمُعَلِّم'), en: 'the book is the teacher’s' })
    expect(at(ofTable({ thing: car, owner: student }), 'of').ar).toBe(nfc('سَيَّارَة الطَّالِب'))
    expect(at(ofTable({ thing: car, owner: student }), 'is').ar).toBe(nfc('السَّيَّارَة لِلطَّالِب'))
  })
  it('builds it wrongly as a beginner does, with no meaning', () => {
    expect(at(table, 'wrong:first:of')).toEqual({ key: 'wrong:first:of', ar: nfc('الْكِتَاب الْمُعَلِّم'), en: null })
    expect(at(table, 'wrong:tanween:of').ar).toBe(nfc('كِتَابٌ الْمُعَلِّم'))
  })
})

describe('dualTable', () => {
  const car = { id: 'car', ar: 'سَيَّارَة', en: 'car' }
  it('says two with ـَانِ, or ـَيْنِ, with ال or without', () => {
    const table = dualTable(book)
    expect(at(table, 'two')).toMatchObject({ ar: nfc('كِتَابَانِ'), en: 'two books' })
    expect(at(table, 'two-yn')).toMatchObject({ ar: nfc('كِتَابَيْنِ'), en: 'two books' })
    expect(at(table, 'the-two')).toMatchObject({ ar: nfc('الْكِتَابَانِ'), en: 'the two books' })
    expect(at(table, 'wrong:ta:two')).toBeUndefined()
  })
  it('writes ة as ت before the ending, and keeping it says nothing', () => {
    expect(at(dualTable(car), 'two').ar).toBe(nfc('سَيَّارَتَانِ'))
    expect(at(dualTable(car), 'the-two').ar).toBe(nfc('السَّيَّارَتَانِ'))
    expect(at(dualTable(car), 'wrong:ta:two')).toEqual({ key: 'wrong:ta:two', ar: nfc('سَيَّارَةَانِ'), en: null })
  })
})
