import { describe, expect, it } from 'vitest'

import { CHECK, MISSED, SAID, WAITING, WRONG } from './follow'
import { weakParts, whyOf } from './markWhy'

describe('why a word is marked', () => {
  it('names the case in one sentence each', () => {
    expect(whyOf({ state: SAID })).toBe('Said right.')
    expect(whyOf({ state: SAID, word: 'أَثِيمًا', said: 'أذيما' })).toMatch(/sound check is sure/)
    expect(whyOf({ state: SAID, word: 'أَثِيمًا', said: 'اثيما' })).toBe('Said right.')
    expect(whyOf({ state: MISSED })).toBe('Not heard.')
    expect(whyOf({ state: WAITING })).toBe('Not reached yet.')
    expect(whyOf({ state: CHECK })).toMatch(/could not confirm/)
  })

  it('tells a different word from the same letters said off', () => {
    expect(whyOf({ state: WRONG, word: 'نَعْبُدُ', said: 'المسكين' })).toBe('A different word was heard.')
    expect(whyOf({ state: WRONG, word: 'نَعْبُدُ', said: 'نَعْبِدُ' })).toMatch(/letters matched/)
  })

  it('points at the underlined part only when there is one', () => {
    const slip = { state: WRONG, word: 'نَعْبُدُ', said: 'نَعْبِدُ' }
    expect(whyOf(slip, true)).toMatch(/at the underlined part/)
    expect(whyOf(slip, false)).not.toMatch(/underlined/)
  })
})

describe('the weak part of a word', () => {
  it('cuts where the ear said the piece starts, not at its first look-alike', () => {
    // اللَّهِ has two lams; the piece starts at the second.
    expect(weakParts('ٱللَّهِ', 'ل', 2)).toEqual(['ٱل', 'لَّ', 'هِ'])
    expect(weakParts('نَعْبُدُ', 'ع', 2)).toEqual(['نَ', 'عْ', 'بُدُ'])
  })

  it('folds alif forms and keeps the page marks', () => {
    expect(weakParts('ٱلرَّحْمَٰنِ', 'ا', 0)).toEqual(['', 'ٱ', 'لرَّحْمَٰنِ'])
  })

  it('has nothing to underline for a lone mark, a piece not there, or no start', () => {
    expect(weakParts('ٱللَّهِ', 'ّ', 3)).toBeNull()
    expect(weakParts('نَعْبُدُ', 'س', 2)).toBeNull()
    expect(weakParts('نَعْبُدُ', 'ع', null)).toBeNull()
    expect(weakParts('نَعْبُدُ', null, 0)).toBeNull()
  })
})
