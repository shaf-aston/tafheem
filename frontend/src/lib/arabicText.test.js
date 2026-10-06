import { describe, expect, it } from 'vitest'

import { joinedOn, mostlyArabic, spokenForm } from './arabicText'

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
