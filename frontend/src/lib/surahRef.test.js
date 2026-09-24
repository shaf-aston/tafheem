import { describe, expect, it } from 'vitest'

import surahs from '../data/surahs.json'
import { CLOSE, ayahProblem, placesNamed, readSurahRef, surahsNamed } from './surahRef'

const top = (text) => readSurahRef(text).matches[0]

describe('readSurahRef', () => {
  it('reads a name and a number as surah and ayah', () => {
    expect(top('Nisa 45')).toMatchObject({ n: 4, en: 'An-Nisa' })
    expect(readSurahRef('Nisa 45').ayah).toBe(45)
    expect(readSurahRef('nisa 4').ayah).toBe(4)
  })

  it('reads the number after a name as the ayah even when it is also a surah number', () => {
    expect(top('nisa 4')).toMatchObject({ n: 4 })
    expect(top('baqarah 4')).toMatchObject({ n: 2 })
    expect(readSurahRef('baqarah 4').ayah).toBe(4)
  })

  it('does not need the article, the hyphen or the apostrophe', () => {
    for (const typed of ['an-nisa 3', 'annisa 3', 'nisa 3', "An Nisa' 3"]) {
      expect(top(typed)).toMatchObject({ n: 4 })
    }
    expect(top("ma'idah 3")).toMatchObject({ n: 5 })
    expect(top('imran 3')).toMatchObject({ n: 3 })
    expect(top('ali imran 3')).toMatchObject({ n: 3 })
  })

  it('forgives the spellings people actually use', () => {
    expect(top('Nisaa 1')).toMatchObject({ n: 4 })
    expect(top('Baqara 255')).toMatchObject({ n: 2 })
    expect(top('Yaseen 9')).toMatchObject({ n: 36 })
    expect(top('Fatiha 1')).toMatchObject({ n: 1 })
    expect(top('Rahman')).toMatchObject({ n: 55 })
  })

  it('accepts the words around a reference', () => {
    expect(top('surah kahf ayah 10')).toMatchObject({ n: 18 })
    expect(readSurahRef('surah kahf ayah 10').ayah).toBe(10)
    expect(readSurahRef('nisa v45').ayah).toBe(45)
  })

  it('takes the ayah after a colon or the last number', () => {
    expect(readSurahRef('nisa 4:45').ayah).toBe(45)
    expect(readSurahRef('nisa:45').ayah).toBe(45)
  })

  it('reads Arabic names and Arabic digits', () => {
    expect(top('النساء ٤٥')).toMatchObject({ n: 4 })
    expect(readSurahRef('النساء ٤٥').ayah).toBe(45)
    expect(top('البقرة 255')).toMatchObject({ n: 2 })
    expect(top('يس')).toMatchObject({ n: 36 })
  })

  it('reads bare numbers as an address', () => {
    expect(readSurahRef('2:255')).toMatchObject({ ayah: 255, matches: [{ n: 2 }] })
    expect(readSurahRef('2 255')).toMatchObject({ ayah: 255, matches: [{ n: 2 }] })
    expect(readSurahRef('36')).toMatchObject({ ayah: null, matches: [{ n: 36 }] })
    expect(readSurahRef('115').matches).toEqual([])
  })

  it('gives a name alone as a surah with no ayah', () => {
    expect(readSurahRef('kahf')).toMatchObject({ ayah: null, matches: [{ n: 18 }] })
  })

  it('says nothing for nothing, and nothing for a non-name', () => {
    expect(readSurahRef('')).toEqual({ matches: [], ayah: null })
    expect(readSurahRef('   ').matches).toEqual([])
    expect(readSurahRef('zzzzqx 4').matches).toEqual([])
  })
})

describe('surahsNamed', () => {
  it('ranks exact before prefix before inside', () => {
    const [first] = surahsNamed('nas')
    expect(first).toMatchObject({ n: 114, close: CLOSE.exact })
    expect(surahsNamed('ka').map((m) => m.close)).toEqual([...surahsNamed('ka').map((m) => m.close)].sort())
  })

  it('offers every surah that starts the same way', () => {
    const names = surahsNamed('ma', 10).map((m) => m.n)
    expect(names).toEqual(expect.arrayContaining([5, 19, 107]))
  })

  it('finds every surah by its own printed name', () => {
    for (const s of surahs) {
      expect(surahsNamed(s.en)[0].n, s.en).toBe(s.n)
      expect(surahsNamed(s.ar)[0].n, s.ar).toBe(s.n)
    }
  })
})

describe('ayahProblem', () => {
  const nisa = surahs[3]
  it('passes an ayah inside the surah, and a missing one', () => {
    expect(ayahProblem(nisa, 176)).toBeNull()
    expect(ayahProblem(nisa, null)).toBeNull()
  })
  it('names the limit when the ayah is past the end', () => {
    expect(ayahProblem(nisa, 177)).toBe('An-Nisa has 176 ayahs')
    expect(ayahProblem(nisa, 0)).toBe('Ayahs start at 1')
  })
})

describe('placesNamed', () => {
  it('names real places only', () => {
    expect(placesNamed('Nisa 45')).toMatchObject([{ ref: '4:45', ayah: 45 }])
    expect(placesNamed('nisa 999')).toEqual([])
    expect(placesNamed('kahf')).toEqual([])
    expect(placesNamed('patience')).toEqual([])
  })
})
