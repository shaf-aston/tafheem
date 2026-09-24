/**
 * A passage of tafsir is commonly written about a run of ayahs, not one. The
 * line above the commentary has to say which run, or four paragraphs about ten
 * ayahs read as four paragraphs about the one that was clicked.
 */
import { describe, expect, it } from 'vitest'

import { passageLabel } from './tafsir'

describe('passageLabel', () => {
  it('names a run by its ends', () => {
    expect(passageLabel(78, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])).toBe('78:1–10')
  })

  it('names a single ayah without a range', () => {
    expect(passageLabel(2, [255])).toBe('2:255')
  })

  it('says nothing rather than half a reference when there is nothing to name', () => {
    expect(passageLabel(2, [])).toBe('')
    expect(passageLabel(2, undefined)).toBe('')
  })
})
