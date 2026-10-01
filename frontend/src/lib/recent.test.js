import { describe, expect, it } from 'vitest'

import { addRecent, readRecent, stripOf } from './recent'

// The registry's shape, in its order: row 1/2 fixed, row 3 only as a recent tab.
const TABS = [
  { id: 'nahw', row: 3, half: true, group: 'language' },
  { id: 'sarf', row: 3, half: true, group: 'language' },
  { id: 'quran', row: 1 },
  { id: 'daleel', row: 1 },
  { id: 'hadith', row: 3 },
  { id: 'dict', row: 1 },
  { id: 'mem', row: 2 },
  { id: 'grow', row: 3 },
  { id: 'quiz', row: 2 },
  { id: 'timelines', row: 3 },
  { id: 'dawah', row: 3 },
  { id: 'colloq', row: 3 },
]
const SEED = ['hadith', 'grow']
const strip = (recent) => stripOf(TABS, recent).map((t) => t.id)
const open = (...picks) => picks.reduce((recent, id) => addRecent(recent, id, TABS), SEED)

describe('recent tabs', () => {
  it('starts as the fixed five, then Hadith and Grow', () => {
    expect(strip(SEED)).toEqual(['quran', 'daleel', 'dict', 'mem', 'quiz', 'hadith', 'grow'])
  })

  it('drops the oldest and adds the new one far right', () => {
    expect(open('timelines')).toEqual(['grow', 'timelines'])
    expect(open('timelines', 'dawah')).toEqual(['timelines', 'dawah'])
    expect(open('timelines', 'dawah', 'colloq')).toEqual(['dawah', 'colloq'])
  })

  it('changes nothing for a fixed tab or one already showing', () => {
    const recent = open('timelines')
    expect(addRecent(recent, 'mem', TABS)).toBe(recent)
    expect(addRecent(recent, 'timelines', TABS)).toBe(recent)
  })

  it('counts a half pair as one recent tab, its partner already showing', () => {
    const recent = open('sarf')
    expect(strip(recent)).toEqual(['quran', 'daleel', 'dict', 'mem', 'quiz', 'grow', 'nahw', 'sarf'])
    expect(addRecent(recent, 'nahw', TABS)).toBe(recent)
  })

  it('reads back what it saved, and starts again from anything broken or stale', () => {
    const recent = open('timelines', 'dawah')
    expect(readRecent(JSON.stringify(recent), TABS, SEED)).toEqual(recent)
    for (const text of ['', 'not json', '5', '{"ids":["grow","hadith"]}', '["grow"]', '["gone","hadith"]',
      '["quran","hadith"]', '["dawah","dawah"]', '["nahw","sarf"]']) {
      expect(readRecent(text, TABS, SEED)).toEqual(SEED)
    }
  })
})
