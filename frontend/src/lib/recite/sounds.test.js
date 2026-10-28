import { describe, expect, it } from 'vitest'
import { asArabic } from './sounds'

describe('sounds written as Arabic', () => {
  it('writes letters, short and long vowels, and doubled letters', () => {
    expect(asArabic(['q', 'u', 'l'])).toBe('قُل')
    expect(asArabic(['ʔ', 'a', 'θ', 'i:', 'm', 'a', 'n'])).toBe('ءَثِيمَن')
    expect(asArabic(['rˤ', 'a', 'bb', 'i'])).toBe('رَبِّ')
    expect(asArabic(['ðˤðˤ', 'a'])).toBe('ظَّ')
  })
  it('shows the ث heard as ذ', () => {
    expect(asArabic(['ʔ', 'a', 'ð', 'i:', 'm'])).toBe('ءَذِيم')
  })
  it('drops what it cannot write', () => {
    expect(asArabic(['Q', 'b'])).toBe('ب')
    expect(asArabic()).toBe('')
  })
})
