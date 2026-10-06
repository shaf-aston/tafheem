import { beforeEach, describe, expect, it, vi } from 'vitest'

import { favoriteKey, toggleFavorite } from './useHadithFavorites'

const store = new Map()
vi.stubGlobal('localStorage', {
  getItem: (k) => store.get(k) ?? null,
  setItem: (k, v) => store.set(k, v),
})

const hadith = { collection: 'bukhari', number: 1, part: '', arabic: 'أ', english: 'a', grades: [{ by: 'Al-Albani', grade: 'Sahih' }], cite: 'https://sunnah.com/bukhari:1' }
const saved = () => JSON.parse(localStorage.getItem('hadith-favorites') || '[]')

describe('starring a hadith', () => {
  beforeEach(() => saved().forEach(toggleFavorite))

  it('keeps the whole hadith, so the Starred view needs no fetch', () => {
    toggleFavorite(hadith)
    expect(saved()).toEqual([hadith])
  })

  it('a second press removes it, and a part letter is a different hadith', () => {
    toggleFavorite(hadith)
    toggleFavorite({ ...hadith, part: 'a' })
    expect(saved().map(favoriteKey)).toEqual(['bukhari:1a', 'bukhari:1'])
    toggleFavorite(hadith)
    expect(saved().map(favoriteKey)).toEqual(['bukhari:1a'])
  })
})
