import { describe, expect, it } from 'vitest'

import { moveDock, readDock } from './dock'

const TABS = ['nahw', 'sarf', 'quran', 'dict', 'grow', 'quiz', 'hadith'].map((id) => ({ id }))
const SEED = ['quran', 'dict', 'grow', 'quiz']

describe('reading the saved bar', () => {
  it('starts from the seed when nothing is saved', () => {
    expect(readDock(null, TABS, SEED)).toEqual(SEED)
    expect(readDock('', TABS, SEED)).toEqual(SEED)
  })

  it('keeps the saved order', () => {
    expect(readDock('quiz,nahw,quran', TABS, SEED)).toEqual(['quiz', 'nahw', 'quran'])
  })

  it('drops tabs that no longer exist, repeats, and anything past the bar size', () => {
    expect(readDock('quran,gone,quran,dict', TABS, SEED)).toEqual(['quran', 'dict'])
    expect(readDock('nahw,sarf,quran,dict,grow', TABS, SEED)).toEqual(['nahw', 'sarf', 'quran', 'dict'])
  })

  it('starts again when nothing saved is usable', () => {
    expect(readDock('gone,also-gone', TABS, SEED)).toEqual(SEED)
  })
})

describe('moving a tab', () => {
  it('reorders within the bar', () => {
    expect(moveDock(SEED, 'quiz', 0, 4)).toEqual(['quiz', 'quran', 'dict', 'grow'])
    expect(moveDock(SEED, 'quran', 3, 4)).toEqual(['dict', 'grow', 'quiz', 'quran'])
  })

  it('swaps a More tab in for the slot it lands on when the bar is full', () => {
    expect(moveDock(SEED, 'nahw', 1, 4)).toEqual(['quran', 'nahw', 'grow', 'quiz'])
  })

  it('adds a More tab when there is room', () => {
    expect(moveDock(['quran', 'dict'], 'nahw', 1, 4)).toEqual(['quran', 'nahw', 'dict'])
    expect(moveDock(['quran'], 'nahw', 3, 4)).toEqual(['quran', 'nahw'])
  })

  it('sends a tab to More', () => {
    expect(moveDock(SEED, 'dict', null, 4)).toEqual(['quran', 'grow', 'quiz'])
  })

  it('never empties the bar', () => {
    expect(moveDock(['quran'], 'quran', null, 4)).toEqual(['quran'])
  })

  it('leaves the list it was given alone', () => {
    const before = [...SEED]
    moveDock(SEED, 'nahw', 0, 4)
    expect(SEED).toEqual(before)
  })
})
