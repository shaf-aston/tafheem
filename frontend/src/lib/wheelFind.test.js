import { describe, expect, it } from 'vitest'

import surahs from '../data/surahs.json'
import { wheelFind } from './wheelFind'

const options = surahs.map((s) => ({ id: s.n, label: s.en, keys: [s.ar] }))
const find = (typed) => options[wheelFind(options, typed)]?.id

describe('wheelFind', () => {
  it('jumps to a number', () => {
    expect(find('4')).toBe(4)
    expect(find('114')).toBe(114)
    expect(find('004')).toBe(4)
  })
  it('finds a name by the start of any word, ignoring case and hyphens', () => {
    expect(find('an')).toBe(4)
    expect(find('nis')).toBe(4)
    expect(find('NISA')).toBe(4)
    expect(find('an-nisa')).toBe(4)
    expect(find('baq')).toBe(2)
    expect(find('imran')).toBe(3)
  })
  it('finds the Arabic name', () => {
    expect(find('البقرة')).toBe(2)
  })
  it('gives nothing for no match, an empty box, or a number out of range', () => {
    expect(wheelFind(options, 'zzz')).toBe(-1)
    expect(wheelFind(options, '  ')).toBe(-1)
    expect(wheelFind(options, '115')).toBe(-1)
    expect(wheelFind(options, '0')).toBe(-1)
  })
})
