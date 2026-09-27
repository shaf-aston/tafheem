import { describe, expect, it } from 'vitest'

import { KIND, readQuranQuery } from './quranIntent'

const read = readQuranQuery

describe('readQuranQuery', () => {
  it('reads an empty box as nothing', () => {
    expect(read('').kind).toBe(KIND.none)
    expect(read('   ').kind).toBe(KIND.none)
  })

  it('reads numbers alone as a place', () => {
    expect(read('2:255')).toMatchObject({ kind: KIND.ayah, ayah: 255, surahs: [{ n: 2 }], problem: null })
    expect(read('2 255')).toMatchObject({ kind: KIND.ayah, ayah: 255 })
    expect(read('٢:٢٥٥')).toMatchObject({ kind: KIND.ayah, ayah: 255, surahs: [{ n: 2 }] })
    expect(read('18')).toMatchObject({ kind: KIND.surah, ayah: null, surahs: [{ n: 18 }] })
  })

  it('says why a number cannot be opened', () => {
    expect(read('115:1').problem).toMatch(/114 surahs/)
    expect(read('1:8').problem).toMatch(/7 ayahs/)
  })

  it('reads Latin letters as a surah name, since the words are searched in Arabic', () => {
    expect(read('Nisa 45')).toMatchObject({ kind: KIND.ayah, ayah: 45, surahs: [{ n: 4 }] })
    expect(read('kahf')).toMatchObject({ kind: KIND.surah, surahs: [{ n: 18 }] })
    expect(read('xyzzy').problem).toMatch(/type them in Arabic/)
  })

  it('reads Arabic with a number or سورة as a place, when the name is close', () => {
    expect(read('النساء ٤٥')).toMatchObject({ kind: KIND.ayah, ayah: 45, surahs: [{ n: 4 }] })
    expect(read('سورة الكهف')).toMatchObject({ kind: KIND.surah, surahs: [{ n: 18 }] })
    expect(read('سوره يس')).toMatchObject({ kind: KIND.surah, surahs: [{ n: 36 }] })
  })

  it('reads other Arabic as the words, offering a surah only when named exactly', () => {
    expect(read('الحمد لله')).toMatchObject({ kind: KIND.text, surahs: [] })
    expect(read('الرحمن')).toMatchObject({ kind: KIND.text, surahs: [{ n: 55 }] })
    expect(read('الكهف')).toMatchObject({ kind: KIND.text, surahs: [{ n: 18 }] })
    expect(read('الكه').surahs).toEqual([])
  })

  it('reads anything vowelled as a quote of the words', () => {
    expect(read('بِسْمِ اللَّهِ').kind).toBe(KIND.text)
    expect(read('ٱلرَّحْمَٰنِ').kind).toBe(KIND.text)
  })

  it('keeps a number in Arabic words that name no surah as the words', () => {
    expect(read('صبر ٣').kind).toBe(KIND.text)
  })
})
