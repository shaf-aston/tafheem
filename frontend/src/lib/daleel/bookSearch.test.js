import { describe, expect, it } from 'vitest'

import { nameMatches } from './bookSearch'

const QUDURI = { name: 'مختصر القدوري', english: 'Mukhtasar al-Quduri' }
const HIDAYA = { name: 'الهداية في شرح بداية المبتدي', english: 'Al-Hidaya fi Sharh Bidayat al-Mubtadi' }
const JALALAYN = { name: 'تفسير الجلالين', english: 'Tafsir al-Jalalayn' }
const CORPUS = { name: 'Quranic Arabic Corpus', english: '' }

describe('finding a book by an English name', () => {
  it('finds the book that started this: kuduri', () => {
    expect(nameMatches(QUDURI, 'kuduri')).toBe(true)
  })

  it('finds it however the reader spells the Arabic q', () => {
    // ق is a q to one writer and a k to another, and a long vowel is doubled
    // by one and not the next. All of these are the same book.
    for (const typed of ['quduri', 'Quduri', 'kuduri', 'qudoori', 'kudoori', 'al-quduri']) {
      expect(nameMatches(QUDURI, typed), typed).toBe(true)
    }
  })

  it('finds a book by the middle of its name, without the article', () => {
    expect(nameMatches(HIDAYA, 'hidaya')).toBe(true)
    expect(nameMatches(HIDAYA, 'bidayat')).toBe(true)
    expect(nameMatches(JALALAYN, 'jalalayn')).toBe(true)
  })

  it('does not eat the al inside a word', () => {
    // Jalalayn and Alfiyya begin with those letters; only a standalone article
    // is dropped, or half the library would lose its name.
    expect(nameMatches(JALALAYN, 'jalal')).toBe(true)
    expect(nameMatches({ name: 'ألفية ابن مالك', english: 'Alfiyya of Ibn Malik' }, 'alfiyya')).toBe(true)
  })

  it('still finds a book whose own name is already English', () => {
    expect(nameMatches(CORPUS, 'corpus')).toBe(true)
    expect(nameMatches(CORPUS, 'quranic')).toBe(true)
  })
})

describe('what must not change', () => {
  it('still matches Arabic typed in Arabic', () => {
    expect(nameMatches(QUDURI, 'القدوري')).toBe(true)
    expect(nameMatches(QUDURI, 'قدوري')).toBe(true)
    expect(nameMatches(HIDAYA, 'الهداية')).toBe(true)
  })

  it('says no to a book that is not it', () => {
    expect(nameMatches(QUDURI, 'jalalayn')).toBe(false)
    expect(nameMatches(JALALAYN, 'quduri')).toBe(false)
    expect(nameMatches(CORPUS, 'hidaya')).toBe(false)
  })

  it('is forgiving about spelling, not about which book it is', () => {
    // The nearest thing to a false match the fold could produce: one letter
    // apart is still a different book, because nothing here measures distance.
    expect(nameMatches(QUDURI, 'kuduro')).toBe(false)
    expect(nameMatches(QUDURI, 'qadiri')).toBe(false)
  })

  it('an empty box is not a filter', () => {
    expect(nameMatches(QUDURI, '')).toBe(true)
    expect(nameMatches(QUDURI, '   ')).toBe(true)
  })

  it('does not fall over on a book with no English name', () => {
    expect(nameMatches({ name: 'شيء', english: undefined }, 'x')).toBe(false)
    expect(nameMatches({ name: 'شيء' }, 'شيء')).toBe(true)
  })
})
