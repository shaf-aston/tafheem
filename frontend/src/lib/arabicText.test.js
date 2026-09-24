import { describe, expect, it } from 'vitest'

import { mostlyArabic } from './arabicText'

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
