import { describe, expect, it } from 'vitest'

import { pieces, spelled } from './spell'

describe('saying a word letter by letter', () => {
  it('keeps each letter with its marks and a long vowel with the letter before it', () => {
    expect(pieces('قَطَاة')).toEqual(['قَ', 'طَا', 'ةْ'])
    expect(pieces('فِتْنَة')).toEqual(['فِ', 'تْ', 'نَ', 'ةْ'])
  })

  it('leaves a written last vowel alone', () => {
    expect(pieces('اِسْتَهَانَ').at(-1)).toBe('نَ')
  })

  it('ends on the whole word, after pauses the voice keeps', () => {
    expect(spelled('أُمَّة')).toBe('أُ، مَّ، ةْ، أُمَّة')
  })
})
