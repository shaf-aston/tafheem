import { describe, expect, it } from 'vitest'

import config from '../dictionary.json'
import { entryLines, paragraphs } from './entryLines'

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

const LETTERS = config.entry['paragraph-letters']
const sentence = (n) => `${'ب'.repeat(n)} .`

describe('paragraphs', () => {
  it('joins lines wrapped at the printed width', () => {
    expect(paragraphs('( علمه - كسمعه :\nعرفه ) هكذا في الصحاح')).toEqual(['( علمه - كسمعه : عرفه ) هكذا في الصحاح'])
  })

  it('gathers sentences until a paragraph is long enough, then starts the next', () => {
    const long = sentence(LETTERS)
    expect(paragraphs(`قال . ${long} تم`)).toEqual([`قال . ${long}`, 'تم'])
  })

  it('does not cut at the dots between the halves of a verse', () => {
    const verse = `${'ب'.repeat(LETTERS)} ... ثم`
    expect(paragraphs(verse)).toEqual([verse])
  })

  it('keeps the break where a book returns to the root', () => {
    expect(paragraphs('أول\n\nثان')).toEqual(['أول', 'ثان'])
  })

  it('reads nothing as no paragraphs', () => {
    expect(paragraphs(undefined)).toEqual([])
    expect(paragraphs('')).toEqual([])
  })
})
