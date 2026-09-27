import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

import surahs from '../data/surahs.json'
import { JUZ_COUNT, juzOf, juzStart } from './juz'

// The backend's own juz file, the one the copy in data/juz.json was cut from.
const backend = JSON.parse(readFileSync(new URL('../../../backend/data/quran/juz.json', import.meta.url)))

describe('juz', () => {
  it('starts every juz where the backend says it does', () => {
    expect(JUZ_COUNT).toBe(30)
    for (const j of backend.juzs) {
      const [surah, range] = Object.entries(j.verse_mapping).sort((a, b) => a[0] - b[0])[0]
      expect(juzStart(j.juz_number), `juz ${j.juz_number}`).toEqual({
        surah: Number(surah),
        ayah: Number(range.split('-')[0]),
      })
    }
  })

  it('puts each boundary on the right side', () => {
    for (let n = 2; n <= JUZ_COUNT; n++) {
      const { surah, ayah } = juzStart(n)
      expect(juzOf(surah, ayah), `start of ${n}`).toBe(n)
      // The ayah just before: the previous one in this surah, or the last of the one before.
      const before = ayah > 1 ? [surah, ayah - 1] : [surah - 1, surahs[surah - 2].ayahs]
      expect(juzOf(...before), `end of ${n - 1}`).toBe(n - 1)
    }
  })

  it('covers the first and last ayahs of the Quran', () => {
    expect(juzOf(1, 1)).toBe(1)
    expect(juzOf(2, 255)).toBe(3)
    expect(juzOf(114, 6)).toBe(30)
  })
})
