import { describe, expect, it } from 'vitest'

import { addRecent, readRecent, stripOf } from './recent'

// The registry's ids, in its order.
const TABS = [
  { id: 'nahw' },
  { id: 'sarf' },
  { id: 'quran' },
  { id: 'daleel' },
  { id: 'hadith' },
  { id: 'dict' },
  { id: 'mem' },
  { id: 'grow' },
  { id: 'quiz' },
  { id: 'timelines' },
  { id: 'dawah' },
  { id: 'colloq' },
]
const FIXED = ['quran', 'nahw', 'sarf', 'dict']
const SEED = ['daleel', 'mem', 'quiz', 'grow']
const strip = (recent) => stripOf(TABS, FIXED, recent).map((t) => t.id)
const open = (...picks) => picks.reduce((recent, id) => addRecent(recent, id, TABS, FIXED), SEED)

describe('recent tabs', () => {
  it('starts as the fixed tabs, then the seed', () => {
    expect(strip(SEED)).toEqual(['quran', 'nahw', 'sarf', 'dict', 'daleel', 'mem', 'quiz', 'grow'])
  })

  it('drops the oldest and adds the new one at the end', () => {
    expect(open('hadith')).toEqual(['mem', 'quiz', 'grow', 'hadith'])
    expect(open('hadith', 'dawah')).toEqual(['quiz', 'grow', 'hadith', 'dawah'])
  })

  it('changes nothing for a fixed tab or one already showing', () => {
    const recent = open('hadith')
    for (const id of ['nahw', 'dict', 'hadith']) expect(addRecent(recent, id, TABS, FIXED)).toBe(recent)
  })

  it('reads back what it saved, and starts again from anything broken or stale', () => {
    const recent = open('hadith', 'dawah')
    expect(readRecent(JSON.stringify(recent), TABS, FIXED, SEED)).toEqual(recent)
    for (const text of ['', 'not json', '5', '{"ids":[]}', '["hadith","grow"]', '["gone","mem","quiz","grow"]',
      '["dict","mem","quiz","grow"]', '["mem","mem","quiz","grow"]']) {
      expect(readRecent(text, TABS, FIXED, SEED)).toEqual(SEED)
    }
  })
})
