import { describe, expect, it } from 'vitest'

import surahs from '../data/surahs.json'
import words from '../../public/words/words.json'
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

  it('reads a reference still being typed as the surah so far, not a mistake', () => {
    expect(read('2:')).toMatchObject({ kind: KIND.surah, surahs: [{ n: 2 }], problem: null })
    expect(read('Nisa ')).toMatchObject({ kind: KIND.surah, surahs: [{ n: 4 }] })
  })

  it('reads a surah name typed with ه for ة or ي for ى', () => {
    expect(read('البقره 255')).toMatchObject({ kind: KIND.ayah, ayah: 255, surahs: [{ n: 2 }] })
    expect(read('سورة الضحي')).toMatchObject({ kind: KIND.surah, surahs: [{ n: 93 }] })
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

  // Every surah, by number, English and Arabic name, at its first and last
  // ayah and one past it: the box must open exactly that place or say why not.
  it('reads every surah at its first ayah, its last, and one past it', () => {
    // The first match is the one Enter opens; near misses may follow it.
    const opens = (typed) => { const r = read(typed); return { kind: r.kind, n: r.surahs[0]?.n, ayah: r.ayah, problem: r.problem } }
    const arDigits = (n) => String(n).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d])
    for (const s of surahs) {
      for (const typed of [`${s.n}:1`, `${s.en} 1`, `${s.ar} ${arDigits(1)}`]) {
        expect(opens(typed), typed).toEqual({ kind: KIND.ayah, n: s.n, ayah: 1, problem: null })
      }
      for (const typed of [`${s.n}:${s.ayahs}`, `${s.en} ${s.ayahs}`, `${s.ar} ${s.ayahs}`]) {
        expect(opens(typed), typed).toEqual({ kind: KIND.ayah, n: s.n, ayah: s.ayahs, problem: null })
      }
      for (const typed of [`${s.n}:${s.ayahs + 1}`, `${s.en} ${s.ayahs + 1}`, `${s.ar} ${s.ayahs + 1}`]) {
        expect(read(typed).problem, typed).toMatch(/ayahs/)
      }
      for (const typed of [String(s.n), s.en, `سورة ${s.ar}`]) {
        expect(opens(typed), typed).toMatchObject({ kind: KIND.surah, n: s.n })
      }
    }
  })

  // The words the Qur'an is made of, vowelled and bare: none may be taken for
  // a place, or a search for it would open an ayah nobody asked for.
  it('searches every word in the word bank as words, never as a place', () => {
    const bare = (t) => t.replace(/[\u0610-\u061A\u064B-\u065F\u0670]/g, '')
    for (const { ar } of words.words) {
      for (const typed of [ar, bare(ar)]) expect(read(typed).kind, typed).toBe(KIND.text)
    }
  })
})
