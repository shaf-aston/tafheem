import { describe, expect, it } from 'vitest'

import { addRecent, keepRecent, readRecent, seedOf, stripOf } from './recent'

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
const open = (...picks) => picks.reduce((recent, id) => addRecent(recent, id, TABS, FIXED), seedOf(SEED))

describe('recent tabs', () => {
  it('starts as the fixed tabs, then the seed', () => {
    expect(strip(seedOf(SEED))).toEqual(['quran', 'nahw', 'sarf', 'dict', 'daleel', 'mem', 'quiz', 'grow'])
  })

  it('puts a new tab in the oldest arrival\'s place, and moves nothing else', () => {
    expect(open('hadith').slots).toEqual(['hadith', 'mem', 'quiz', 'grow'])
    expect(open('hadith', 'dawah').slots).toEqual(['hadith', 'dawah', 'quiz', 'grow'])
    // Round the slots and back to the first: hadith was the oldest arrival by then.
    expect(open('hadith', 'dawah', 'colloq', 'timelines', 'sarf').slots).toEqual(['hadith', 'dawah', 'colloq', 'timelines'])
    expect(open('hadith', 'dawah', 'colloq', 'timelines', 'daleel').slots).toEqual(['daleel', 'dawah', 'colloq', 'timelines'])
  })

  it('keeps every other tab on its number key when one is replaced', () => {
    const before = strip(open('hadith'))
    const after = strip(open('hadith', 'dawah'))
    const moved = before.filter((id, at) => after[at] !== id)
    expect(moved).toEqual(['mem'])
  })

  it('changes nothing for a fixed tab or one already showing', () => {
    const recent = open('hadith')
    for (const id of ['nahw', 'dict', 'hadith']) expect(addRecent(recent, id, TABS, FIXED)).toBe(recent)
  })

  it('reads back what it saved, and starts again from anything broken or stale', () => {
    const recent = open('hadith', 'dawah')
    expect(readRecent(JSON.stringify(recent), TABS, FIXED, SEED)).toEqual(recent)
    // An older save, the bare list, is still read: the next new tab takes its first slot.
    expect(readRecent('["hadith","mem","quiz","grow"]', TABS, FIXED, SEED)).toEqual({ slots: ['hadith', 'mem', 'quiz', 'grow'], next: 0 })
    for (const text of ['', 'not json', '5', '{"ids":[]}', '["hadith","grow"]', '["gone","mem","quiz","grow"]',
      '["dict","mem","quiz","grow"]', '["mem","mem","quiz","grow"]',
      '{"slots":["hadith","mem","quiz","grow"],"next":4}', '{"slots":["hadith","mem","quiz","grow"],"next":-1}']) {
      expect(readRecent(text, TABS, FIXED, SEED)).toEqual(seedOf(SEED))
    }
  })
})

describe('keepRecent', () => {
  it('puts the tab last, without a repeat', () => {
    expect(keepRecent(['a', 'b', 'c'], 'a', 4)).toEqual(['b', 'c', 'a'])
  })

  it('drops the oldest past the limit', () => {
    expect(keepRecent(['a', 'b', 'c', 'd'], 'e', 4)).toEqual(['b', 'c', 'd', 'e'])
  })
})
