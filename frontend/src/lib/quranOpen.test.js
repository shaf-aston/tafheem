import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

import { quranOpen } from './quranOpen'
import { DEFAULT_TRANSLATION, editionFor } from './useTranslation'

describe('editionFor', () => {
  it('trusts the saved book before the list comes, else the default', () => {
    expect(editionFor('pickthall-en', null)).toBe('pickthall-en')
    expect(editionFor('', null)).toBe(DEFAULT_TRANSLATION)
  })

  it('falls back to the first installed book once the list is here', () => {
    expect(editionFor('gone', ['a', 'b'])).toBe('a')
    expect(editionFor('b', ['a', 'b'])).toBe('b')
    expect(editionFor('b', [])).toBe('')
  })

  it('the default is the first translation the library lists', () => {
    const manifest = JSON.parse(readFileSync(new URL('../../../backend/data/quran/editions.json', import.meta.url)))
    const first = Object.entries(manifest).find(([, book]) => book?.kind === 'translation')
    expect(first[0]).toBe(DEFAULT_TRANSLATION)
  })
})

describe('quranOpen', () => {
  it('asks for the surah, glosses, books and translation together', () => {
    const keys = []
    quranOpen({ prefetchQuery: (q) => keys.push(q.queryKey) }, '2:255')
    expect(keys).toEqual([
      ['quran-surah', 2],
      ['surah-glosses', 2],
      ['quran-editions', 'translation'],
      ['surah-edition', 2, DEFAULT_TRANSLATION],
    ])
  })

  it('asks for nothing with no place to open on', () => {
    const keys = []
    quranOpen({ prefetchQuery: (q) => keys.push(q.queryKey) }, 'not a place')
    expect(keys).toEqual([])
  })
})
