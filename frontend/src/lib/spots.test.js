import { describe, expect, it } from 'vitest'

import { place, read, stripOf } from './spots'

// The registry's shape, in its order: row 1/2 fixed, row 3 only through a spot.
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
const SEED = ['grow', 'hadith']
const start = read('', TABS, SEED)
const ids = (spots) => stripOf(TABS, spots).map((t) => t.id)
const open = (...picks) => picks.reduce((spots, id) => place(spots, id, TABS), start)

describe('tab spots', () => {
  it('starts as the fixed five, then Grow and Hadith at the far right', () => {
    expect(ids(start)).toEqual(['quran', 'daleel', 'dict', 'mem', 'quiz', 'grow', 'hadith'])
  })

  it('takes the spot held longest, in place', () => {
    expect(open('timelines').ids).toEqual(['grow', 'timelines'])
    expect(open('timelines', 'dawah').ids).toEqual(['dawah', 'timelines'])
    expect(open('timelines', 'dawah', 'colloq').ids).toEqual(['dawah', 'colloq'])
  })

  it('changes nothing for a fixed tab or one already showing', () => {
    const spots = open('timelines')
    expect(place(spots, 'mem', TABS)).toBe(spots)
    expect(place(spots, 'timelines', TABS)).toBe(spots)
  })

  it('fills one spot with a half pair, and its partner is already showing', () => {
    const spots = open('sarf')
    expect(ids(spots)).toEqual(['quran', 'daleel', 'dict', 'mem', 'quiz', 'grow', 'nahw', 'sarf'])
    expect(place(spots, 'nahw', TABS)).toBe(spots)
  })

  it('reads back what it saved, and starts again from anything broken or stale', () => {
    const spots = open('timelines', 'dawah')
    expect(read(JSON.stringify(spots), TABS, SEED)).toEqual(spots)
    for (const text of ['not json', '{"ids":["grow"],"next":0}', '{"ids":["gone","hadith"],"next":0}',
      '{"ids":["quran","hadith"],"next":0}', '{"ids":["dawah","dawah"],"next":0}',
      '{"ids":["nahw","sarf"],"next":0}', '{"ids":["grow","hadith"],"next":2}']) {
      expect(read(text, TABS, SEED)).toEqual(start)
    }
  })
})
