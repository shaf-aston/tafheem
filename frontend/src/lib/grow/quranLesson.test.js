import { describe, expect, it, vi } from 'vitest'

import { bare } from '../quiz/gap'
import { keyOfAyah, loadSurahs, quranCards } from './quranLesson'
import { makeRandom } from '../quiz/quiz'

vi.mock('../../api', () => ({
  getQuranSurah: async (surah) => ({
    surah, name_en: `Surah ${surah}`, name_ar: `س${surah}`,
    ayahs: [1, 2].map((ayah) => ({ ayah, arabic: `ar${surah}:${ayah}`, english: `en${surah}:${ayah}`, page: 1 })),
  }),
}))

const ayah = (surah, n, arabic) => ({ surah, ayah: n, arabic, english: 'x', name_en: 'Surah', name_ar: 'س' })
const ALL = [
  ayah(112, 1, 'قُلْ هُوَ ٱللَّهُ أَحَدٌ ۝١'),
  ayah(112, 2, 'ٱللَّهُ ٱلصَّمَدُ ۝٢'),
  ayah(112, 3, 'لَمْ يَلِدْ وَلَمْ يُولَدْ ۝٣'),
  ayah(112, 4, 'وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ ۝٤'),
  ayah(103, 1, 'وَٱلْعَصْرِ ۝١'),
]

describe('loadSurahs', () => {
  it('flattens the surahs in the order given', async () => {
    const got = await loadSurahs([112, 1])
    expect(got.map(keyOfAyah)).toEqual(['112:1', '112:2', '1:1', '1:2'])
    expect(got[0]).toEqual({ surah: 112, ayah: 1, arabic: 'ar112:1', english: 'en112:1', name_en: 'Surah 112', name_ar: 'س112' })
  })
})

describe('quranCards', () => {
  it('teaches a new ayah, then asks for its missing word', () => {
    const cards = quranCards({ fresh: [ALL[0]], reviews: [] }, ALL, makeRandom(1))
    expect(cards.map((c) => c.kind)).toEqual(['ayah', 'gap'])
    expect(cards.map((c) => c.tag)).toEqual(['New ayah', 'New ayah'])
    expect(cards[0].ayah).toBe(ALL[0])
    expect(cards[1].record).toEqual({ module: 'quran-ayat', item: '112:1', context: { world: 'quran', ask: 'gap' } })
  })

  it('asks a review with a gap card only', () => {
    const cards = quranCards({ fresh: [], reviews: [ALL[2]] }, ALL, makeRandom(2))
    expect(cards.map((c) => [c.kind, c.tag])).toEqual([['gap', 'Review']])
  })

  it('blanks a word of the ayah, marks and end number set aside', () => {
    for (const one of ALL) {
      const [, gap] = quranCards({ fresh: [one], reviews: [] }, ALL, makeRandom(3))
      expect(gap.gap.words.join(' ')).not.toMatch(/[۝١٢٣٤]/)
      expect(one.arabic).toContain(gap.answerText)
      expect(gap.gap.options.map((o) => o.text)).toContain(gap.answerText)
      expect(new Set(gap.gap.options.map((o) => bare(o.text))).size).toBe(gap.gap.options.length)
    }
  })

  it('works for a one-word ayah', () => {
    const [, gap] = quranCards({ fresh: [ALL[4]], reviews: [] }, ALL, makeRandom(4))
    expect(gap.gap).toMatchObject({ at: 0, answer: 'وَٱلْعَصْرِ', words: ['وَٱلْعَصْرِ'] })
    expect(gap.gap.options).toHaveLength(4)
  })
})
