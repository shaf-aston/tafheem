import { describe, expect, it } from 'vitest'

import { plainPronunciation } from './pronounce'

describe('spelling a word the way it sounds', () => {
  it('writes the two-letter sounds English already uses', () => {
    expect(plainPronunciation('šams')).toBe('shams')
    expect(plainPronunciation('ṯalāṯa')).toBe('thalaatha')
    expect(plainPronunciation('ḵabaza')).toBe('khabaza')
    expect(plainPronunciation('ḡurfa')).toBe('ghurfa')
    expect(plainPronunciation('ḏahab')).toBe('dhahab')
  })

  it('doubles a long vowel instead of marking it', () => {
    // Length is grammar here, not decoration: dropping it would make faʕala
    // and faaʕala the same word on screen.
    expect(plainPronunciation('kitāb')).toBe('kitaab')
    expect(plainPronunciation('ḥadīqa')).toBe('hadeeqa')
    expect(plainPronunciation('ṭālib')).toBe('taalib')
  })

  it('prints an emphatic letter as its plain English neighbour', () => {
    expect(plainPronunciation('ṣaḥrāʔ')).toBe("sahraa'")
    expect(plainPronunciation('ẓahara')).toBe('zahara')
    expect(plainPronunciation('ḍarb')).toBe('darb')
  })

  it('drops the catch that opens a word but keeps one you can hear', () => {
    expect(plainPronunciation('ʔamīr')).toBe('ameer')
    expect(plainPronunciation('ʕarabiyya')).toBe('arabiyya')
    expect(plainPronunciation('al-ʔamr')).toBe('al-amr')
    expect(plainPronunciation('masʔala')).toBe("mas'ala")
    expect(plainPronunciation('samāʔ')).toBe("samaa'")
  })

  it('leaves the joined article joined', () => {
    // š-šarqiyya is one word said "sh-sharqiyya"; the hyphen is the assimilated
    // al-, and losing it would hide why the sh is doubled.
    expect(plainPronunciation('ʔūrūbbā š-šarqiyya')).toBe('ooroobbaa sh-sharqiyya')
  })

  it('reads a letter that arrived as a mark of its own', () => {
    // The same h-with-a-dot-under: once as a single character, once as a plain
    // h with the dot as a mark of its own. Both must read as h.
    expect(plainPronunciation('ḥubb')).toBe('hubb')
    expect(plainPronunciation('ḥubb')).toBe('hubb')
  })

  it('reads the romanisations buried inside a definition', () => {
    // Wiktionary writes them mid-sentence, and the pronunciation line above the
    // entry says the same word: two spellings of one sound on one card is the
    // confusion this exists to stop.
    expect(plainPronunciation('verbal noun of كَاتَبَ (kātaba) (form III)'))
      .toBe('verbal noun of كَاتَبَ (kaataba) (form III)')
    expect(plainPronunciation('genitive/possessive construction, ʾiḍāfa'))
      .toBe('genitive/possessive construction, idaafa')
  })

  it('leaves a sound written as IPA alone', () => {
    // The sentence is about that symbol; rewriting it would make it false.
    expect(plainPronunciation('Hamza (ء) represents the glottal stop /ʔ/.'))
      .toBe('Hamza (ء) represents the glottal stop /ʔ/.')
  })

  it('keeps the letter a definition is naming, rather than emptying the brackets', () => {
    expect(plainPronunciation('ا (ʔ), و (w) and ي (y)')).toBe("ا ('), و (w) and ي (y)")
  })

  it('shows a symbol it has never met rather than dropping it', () => {
    expect(plainPronunciation('kitābǝ')).toBe('kitaabǝ')
  })

  it('has nothing to say about nothing', () => {
    expect(plainPronunciation('')).toBe('')
    expect(plainPronunciation(null)).toBe('')
    expect(plainPronunciation(undefined)).toBe('')
  })
})
