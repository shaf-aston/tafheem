import { describe, expect, it } from 'vitest'

import { CHECK, MISSED, SAID, WRONG } from './follow'
import { weakParts, whyOf } from './markWhy'

describe('why a word is marked', () => {
  it('names the case in one sentence each', () => {
    expect(whyOf({ state: SAID })).toBe('Said right.')
    expect(whyOf({ state: MISSED })).toBe('Not heard.')
    expect(whyOf({ state: CHECK })).toMatch(/could not confirm/)
  })

  it('tells a different word from the same letters said off', () => {
    expect(whyOf({ state: WRONG, word: 'نَعْبُدُ', said: 'المسكين' })).toBe('A different word was heard.')
    expect(whyOf({ state: WRONG, word: 'نَعْبُدُ', said: 'نَعْبِدُ' })).toMatch(/letters matched/)
  })
})

describe('the weak part of a word', () => {
  it('finds a plainly spelt piece in the printed word and keeps the printed marks', () => {
    expect(weakParts('نَعْبُدُ', 'عب')).toEqual(['نَ', 'عْبُ', 'دُ'])
  })

  it('takes the marks that trail the last letter of the piece', () => {
    expect(weakParts('نَعْبُدُ', 'ن')).toEqual(['', 'نَ', 'عْبُدُ'])
  })

  it('folds alif forms and ignores a piece that is only marks or not there', () => {
    expect(weakParts('ٱلرَّحْمَٰنِ', 'الر')).toEqual(['', 'ٱلرَّ', 'حْمَٰنِ'])
    expect(weakParts('نَعْبُدُ', 'ـَ')).toBeNull()
    expect(weakParts('نَعْبُدُ', 'سس')).toBeNull()
    expect(weakParts('نَعْبُدُ', null)).toBeNull()
  })
})
