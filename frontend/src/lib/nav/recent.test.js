import { describe, expect, it } from 'vitest'

import { keepRecent, stripOf } from './recent'

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
const strip = (active) => stripOf(TABS, FIXED, SEED, active).map((t) => t.id)
const STEADY = ['quran', 'nahw', 'sarf', 'dict', 'daleel', 'mem', 'quiz', 'grow']

describe('the strip', () => {
  it('is the fixed tabs, then the seed, whichever of them is open', () => {
    for (const id of STEADY) expect(strip(id)).toEqual(STEADY)
  })

  it('shows an open tab that is off the strip after them, and moves nothing', () => {
    expect(strip('hadith')).toEqual([...STEADY, 'hadith'])
    expect(strip('dawah')).toEqual([...STEADY, 'dawah'])
  })

  it('adds nothing for a tab that is not listed (a hidden one)', () => {
    expect(strip('kit')).toEqual(STEADY)
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
