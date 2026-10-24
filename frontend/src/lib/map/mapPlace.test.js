import { describe, expect, it } from 'vitest'

import { placeOf, reachable, screenOf, upOf, valueOf } from './mapPlace'

const CHARTS = [{ id: '07', en: 'Arabic Language' }, { id: '01', en: 'Fiqh' }]
const FAMILIES = [
  { id: 'creed', en: 'Creed schools', groups: [{ id: 'athari', en: 'Atharī' }, { id: 'ibadi', en: 'Ibāḍī' }] },
  { id: 'fiqh', en: 'Schools of law', groups: [{ id: 'hanafi', en: 'Ḥanafī' }] },
]
const place = (value) => placeOf(value, CHARTS, FAMILIES)

describe('a Map address', () => {
  it('reads every screen and writes it back the same', () => {
    for (const value of [null, '07', '07/2/0', 'manhaj/creed', 'manhaj/creed/ibadi', 'manhaj/creed/ibadi/athari']) {
      expect(valueOf(place(value)), String(value)).toBe(value)
    }
    expect(place('07/2/0')).toEqual({ at: 'chart', id: '07', path: [2, 0] })
    expect(place('manhaj/creed/ibadi/athari')).toEqual({ at: 'manhaj', family: 'creed', group: 'ibadi', other: 'athari' })
  })

  it('falls back to the nearest place that exists', () => {
    expect(place('nothing')).toEqual({ at: 'index' })
    expect(place('07/2/x/1')).toEqual({ at: 'chart', id: '07', path: [2] })
    expect(place('manhaj')).toEqual({ at: 'manhaj', family: 'creed' })
    expect(place('manhaj/nope/ibadi')).toEqual({ at: 'manhaj', family: 'creed' })
    expect(place('manhaj/creed/nope')).toEqual({ at: 'manhaj', family: 'creed' })
    // A group from another family, or compared with itself, is not a comparison.
    expect(place('manhaj/creed/ibadi/hanafi')).toEqual({ at: 'manhaj', family: 'creed', group: 'ibadi' })
    expect(place('manhaj/creed/ibadi/ibadi')).toEqual({ at: 'manhaj', family: 'creed', group: 'ibadi' })
  })

  it('keeps the part of a zoom path the chart still has', () => {
    const tree = { kids: [{ kids: [{ kids: [] }] }] }
    expect(reachable(tree, [0, 0])).toEqual([0, 0])
    expect(reachable(tree, [0, 3, 1])).toEqual([0])
    expect(reachable(tree, [5])).toEqual([])
  })

  it('goes up one level at a time', () => {
    expect(upOf(place('07/2/0'))).toEqual(place('07/2'))
    expect(upOf(place('07'))).toEqual({ at: 'index' })
    expect(upOf(place('manhaj/creed/ibadi/athari'))).toEqual(place('manhaj/creed'))
    expect(upOf(place('manhaj/fiqh'))).toEqual({ at: 'index' })
  })

  it('counts a comparison as the same screen, and a zoom or a group as a new one', () => {
    expect(screenOf(place('manhaj/creed/ibadi/athari'))).toBe(screenOf(place('manhaj/creed/ibadi')))
    expect(screenOf(place('manhaj/creed/ibadi'))).not.toBe(screenOf(place('manhaj/creed')))
    expect(screenOf(place('07/1'))).not.toBe(screenOf(place('07')))
    expect(screenOf({ at: 'index' })).toBe('')
  })
})
