import { describe, expect, it } from 'vitest'

import QURAN from '../../config/quran.json'
import { isAyah } from './surahRef'
import { todayAyah } from './todayAyah'

const REFS = ['1:1', '2:255', '112:1']

describe('todayAyah', () => {
  it('is the same ayah all day', () => {
    const morning = todayAyah(new Date(2026, 10, 7, 0, 1), REFS)
    expect(todayAyah(new Date(2026, 10, 7, 23, 59), REFS)).toEqual(morning)
  })

  it('moves to the next reference each day, and wraps round', () => {
    const days = [7, 8, 9, 10].map((day) => todayAyah(new Date(2026, 10, day, 12), REFS))
    const at = REFS.indexOf(`${days[0].surah}:${days[0].ayah}`)
    expect(days.map((d) => `${d.surah}:${d.ayah}`)).toEqual([0, 1, 2, 3].map((step) => REFS[(at + step) % REFS.length]))
  })

  it('counts a day across a clock change as one day', () => {
    // 29 and 30 March straddle the spring change in Europe; either way, two days apart from the 28th.
    const [a, b, c] = [28, 29, 30].map((day) => todayAyah(new Date(2026, 2, day, 12), REFS))
    expect(new Set([a, b, c].map((d) => `${d.surah}:${d.ayah}`)).size).toBe(3)
  })

  it('every configured reference is a real ayah', () => {
    expect(QURAN.today.length).toBeGreaterThan(7)
    for (const ref of QURAN.today) {
      const [surah, ayah] = ref.split(':').map(Number)
      expect(isAyah({ surah, ayah }), ref).toBe(true)
    }
    expect(new Set(QURAN.today).size).toBe(QURAN.today.length)
  })
})
