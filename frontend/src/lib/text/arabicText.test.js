import { describe, expect, it } from 'vitest'

import { foldForSearch, isOneArabicWord, joinedOn, mostlyArabic, unpunctuated, untrailed } from './arabicText'

describe('mostlyArabic', () => {
  it('is true for an ayah', () => {
    expect(mostlyArabic('وَأَقِيمُوا الصَّلَاةَ')).toBe(true)
  })

  it("is false for Lane's English with Arabic words in it", () => {
    expect(mostlyArabic('شَرِكَهُ فِيهِ, aor. شَرَكَ, inf. n. شِرْكَةٌ, the former a contraction')).toBe(false)
  })

  it('is true for Arabic with a stray Latin page mark', () => {
    // The nearest case the other way: a classical book's Arabic with a locator.
    expect(mostlyArabic('قال سيبويه هذا باب ما يكون فيه الاسم مبنيا PageV01P012')).toBe(true)
  })

  it('is false for nothing', () => {
    expect(mostlyArabic('')).toBe(false)
    expect(mostlyArabic(undefined)).toBe(false)
  })
})

describe('joinedOn', () => {
  it('gives a piece the joining stroke only when its last letter joins on', () => {
    expect(joinedOn('فَ')).toBe('فَـ')
    expect(joinedOn('لْ')).toBe('لْـ')
    expect(joinedOn('وَ')).toBe('وَ') // و never joins the letter after it
    expect(joinedOn('بِ')).toBe('بِـ')
  })
})

describe('punctuation in a search', () => {
  it('is a break between words, never part of one', () => {
    expect(unpunctuated('يوم القيامة.')).toBe('يوم القيامة ')
    expect(unpunctuated('مالك،يوم')).toBe('مالك يوم')
    expect(unpunctuated("don't (state)")).toBe("don't state ")
    expect(foldForSearch('Mercy.')).toBe('mercy ')
    expect(foldForSearch('mercy. peace')).toBe(foldForSearch('mercy peace'))
  })

  it('trails off a typed line, leaving a command prefix alone', () => {
    expect(untrailed(' 2:255. ')).toBe('2:255')
    expect(untrailed('الفاتحة؟')).toBe('الفاتحة')
    expect(untrailed('2:')).toBe('2')
    expect(untrailed('@')).toBe('@')
    expect(untrailed('/')).toBe('/')
  })
})

// The same answer as the backend's arabic_word, which /api/morphology/meaning refuses by.
describe('isOneArabicWord', () => {
  it('takes one word however it is dressed', () => {
    for (const word of ['كتب', 'وَكَتَبَ', 'فَسَيَكْفِيكَهُمُ', 'ٱلۡكِتَٰبُ', 'رَيۡبَۛ', 'ـكتب', 'كتب؟', '(كتب)', ' كتب ', 'پاکستان']) {
      expect(isOneArabicWord(word), word).toBe(true)
    }
  })

  it('refuses two words, a root spelled out, and another script', () => {
    for (const text of ['ذهب الولد', 'ك-ت-ب', 'ك ت ب', 'كتب،قلم', 'Ignoreب', 'كتب book', 'кتاب', '', '  ', '١٢', undefined]) {
      expect(isOneArabicWord(text), String(text)).toBe(false)
    }
  })

  it('does not count a pause sign as a word', () => {
    expect(isOneArabicWord('۞ كتب')).toBe(true)
  })
})
