import { describe, expect, it } from 'vitest'

import { placeOf, valueOf } from './growPlace'

const WORLDS = ['words', 'prayer', 'quran', 'hadith']
const LESSONS = ['words', 'quran', 'hadith']
const BOOKS_WORLDS = [...WORLDS, 'fiqh']
const BOOKS = ['fiqh']

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

describe('a book world', () => {
  const at = (value) => placeOf(value, BOOKS_WORLDS, LESSONS, BOOKS)

  it('reads its parts, a lesson in a part, and the review', () => {
    expect(at('fiqh')).toEqual({ at: 'world', id: 'fiqh' })
    expect(at('fiqh/tahara')).toEqual({ at: 'world', id: 'fiqh', part: 'tahara' })
    expect(at('fiqh/tahara/wudu')).toEqual({ at: 'lesson', id: 'fiqh', part: 'tahara', lesson: 'wudu' })
    expect(at('fiqh/review')).toEqual({ at: 'lesson', id: 'fiqh', lesson: 'review' })
  })

  it('falls back to the world on an address too deep', () => {
    expect(at('fiqh/tahara/wudu/more')).toEqual({ at: 'world', id: 'fiqh' })
    expect(at('fiqh/review/more')).toEqual({ at: 'world', id: 'fiqh' })
  })

  it('round-trips every screen', () => {
    for (const view of [
      { at: 'world', id: 'fiqh' },
      { at: 'world', id: 'fiqh', part: 'tahara' },
      { at: 'lesson', id: 'fiqh', part: 'tahara', lesson: 'wudu' },
      { at: 'lesson', id: 'fiqh', lesson: 'review' },
    ]) expect(at(valueOf(view))).toEqual(view)
  })
})
