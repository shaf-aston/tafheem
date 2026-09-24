import { describe, expect, it } from 'vitest'

import { entryLines } from './entryLines'

describe('entryLines', () => {
  it('gives back one line per line the book broke', () => {
    expect(entryLines('أول\nثان\nثالث')).toHaveLength(3)
  })

  it('splits a verse into its two printed halves', () => {
    const [line] = entryLines('جِذْمُنَا قَيْسٌ ... وَلَنَا الْأَبُّ')
    expect(line.halves).toEqual(['جِذْمُنَا قَيْسٌ', 'وَلَنَا الْأَبُّ'])
  })

  it('leaves prose whole, there is nothing inside it to lay out', () => {
    const [line] = entryLines('مِنْ ذَلِكَ الْكِتَابُ وَالْكِتَابَةُ.')
    expect(line.halves).toBeNull()
  })

  // Three gaps is not a verse in two halves, and cutting it anywhere would be
  // a guess at where the poet stopped. It stays one line.
  it('does not cut a line that has more than one gap in it', () => {
    const [line] = entryLines('أ ... ب ... ج')
    expect(line.halves).toBeNull()
    expect(line.text).toBe('أ ... ب ... ج')
  })

  it('drops blank lines rather than printing empty space', () => {
    expect(entryLines('أول\n\n   \nثان')).toHaveLength(2)
  })

  it('has nothing to show for an entry with no rest', () => {
    expect(entryLines('')).toEqual([])
    expect(entryLines(undefined)).toEqual([])
  })
})
