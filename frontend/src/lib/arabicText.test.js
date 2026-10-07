import { describe, expect, it } from 'vitest'

import { foldForSearch, joinedOn, mostlyArabic, spokenForm, unpunctuated, untrailed } from './arabicText'

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

describe('spokenForm', () => {
  // Single letters and marks only: no Arabic phrases are authored in tests.
  it('drops harakat and tatweel', () => expect(spokenForm('هَـ')).toBe('ه'))
  it('folds hamza on alif, ى and ة', () => expect(spokenForm('أ إ آ ى ة')).toBe('ا ا ا ي ه'))
  it('turns punctuation into one space and trims', () => expect(spokenForm(' ه،  ه؟ ')).toBe('ه ه'))
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
