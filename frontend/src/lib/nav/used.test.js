import { describe, expect, it } from 'vitest'

import config from '../../config/session.json'
import { addUse, orderByUse, readUses } from './used'

const TABS = ['home', 'nahw', 'sarf', 'quran', 'daleel', 'hadith', 'dict', 'mem', 'quiz', 'colloq'].map((id) => ({ id }))
const PLACES = ['home', 'quran', 'nahw', 'sarf', 'dict', 'daleel', 'mem', 'quiz']
const ENOUGH = config['tab-uses-to-order']
const many = (id, n) => Array(n).fill(id)

describe('readUses', () => {
  it('drops tabs that no longer exist', () => {
    expect(readUses('quran,gone,dict', TABS)).toEqual(['quran', 'dict'])
  })

  it('reads nothing as no choices', () => {
    expect(readUses(null, TABS)).toEqual([])
  })
})

describe('addUse', () => {
  it('drops the oldest past the kept number', () => {
    const full = many('quran', config['tab-uses-kept'])
    expect(addUse(full, 'dict').at(-1)).toBe('dict')
    expect(addUse(full, 'dict')).toHaveLength(config['tab-uses-kept'])
  })
})

describe('orderByUse', () => {
  it('keeps the default strip until there are enough choices', () => {
    expect(orderByUse(TABS, PLACES, many('colloq', ENOUGH - 1), 'home')).toBe(PLACES)
  })

  it('keeps Home first, then the most chosen', () => {
    const uses = [...many('colloq', 5), ...many('hadith', 3), ...many('dict', 1)]
    const strip = orderByUse(TABS, PLACES, uses, 'home')
    expect(strip.slice(0, 4)).toEqual(['home', 'colloq', 'hadith', 'dict'])
    expect(strip).toHaveLength(PLACES.length)
  })

  it('fills the rest in the default order, so a little use changes only a little', () => {
    const strip = orderByUse(TABS, PLACES, many('colloq', ENOUGH), 'home')
    expect(strip).toEqual(['home', 'colloq', 'quran', 'nahw', 'sarf', 'dict', 'daleel', 'mem'])
  })

  it('never lists Home twice, however often it was chosen', () => {
    const strip = orderByUse(TABS, PLACES, many('home', ENOUGH), 'home')
    expect(strip.filter((id) => id === 'home')).toHaveLength(1)
  })
})
