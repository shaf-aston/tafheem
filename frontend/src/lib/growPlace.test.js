import { describe, expect, it } from 'vitest'

import { placeOf, valueOf } from './growPlace'

const WORLDS = ['words', 'prayer', 'quran', 'hadith']
const LESSONS = ['words', 'quran', 'hadith']

describe('placeOf', () => {
  it('reads home, a world and a lesson', () => {
    expect(placeOf(null, WORLDS, LESSONS)).toEqual({ at: 'home' })
    expect(placeOf('hadith', WORLDS, LESSONS)).toEqual({ at: 'world', id: 'hadith' })
    expect(placeOf('quran/lesson', WORLDS, LESSONS)).toEqual({ at: 'lesson', id: 'quran' })
  })

  it('falls back rather than failing on a stray address', () => {
    expect(placeOf('nowhere', WORLDS, LESSONS)).toEqual({ at: 'home' })
    expect(placeOf('prayer/lesson', WORLDS, LESSONS)).toEqual({ at: 'world', id: 'prayer' })
    expect(placeOf('hadith/other', WORLDS, LESSONS)).toEqual({ at: 'world', id: 'hadith' })
    expect(placeOf('hadith/lesson/3', WORLDS, LESSONS)).toEqual({ at: 'home' })
  })
})

describe('valueOf', () => {
  it('round-trips every screen', () => {
    for (const view of [{ at: 'home' }, { at: 'world', id: 'prayer' }, { at: 'lesson', id: 'words' }]) {
      expect(placeOf(valueOf(view), WORLDS, LESSONS)).toEqual(view)
    }
  })
})
