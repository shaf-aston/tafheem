import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  fillShelf, forgetKey, forgetProgressKeys, onChange, progressKey, readRaw, readSaved, shelfOf, writeRaw, writeSaved,
} from './stored'

let data
beforeEach(() => {
  data = new Map()
  vi.stubGlobal('localStorage', {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: (k) => data.delete(k),
    get length() { return data.size },
    key: (i) => [...data.keys()][i] ?? null,
  })
})
afterEach(() => vi.unstubAllGlobals())

describe('stored', () => {
  it('forgets every progress record and nothing else', () => {
    writeRaw(progressKey('grow-record'), '{}')
    writeRaw(progressKey('tamreen-answers'), '{}')
    writeRaw('settings', '{}')
    writeRaw('reciter', 'alafasy')
    forgetProgressKeys()
    expect([...data.keys()]).toEqual(['settings', 'reciter'])
  })

  it('round-trips JSON', () => {
    writeSaved('k', { a: [1, 2] })
    expect(data.get('k')).toBe('{"a":[1,2]}')
    expect(readSaved('k', null)).toEqual({ a: [1, 2] })
  })

  it('gives the fallback for a missing key', () => {
    expect(readSaved('nope', 'fb')).toBe('fb')
    expect(readRaw('nope')).toBe('')
  })

  it('gives the fallback for corrupt JSON', () => {
    data.set('k', '{oops')
    expect(readSaved('k', [])).toEqual([])
  })

  it('keeps a raw string exactly as written', () => {
    writeRaw('k', 'on')
    expect(data.get('k')).toBe('on')
    expect(readRaw('k')).toBe('on')
  })

  it('forgets one key', () => {
    writeRaw('k', 'x')
    forgetKey('k')
    expect(data.has('k')).toBe(false)
  })

  it('never throws when storage does', () => {
    const boom = () => { throw new Error('denied') }
    vi.stubGlobal('localStorage', { getItem: boom, setItem: boom, removeItem: boom })
    expect(readSaved('k', 'fb')).toBe('fb')
    expect(readRaw('k', 'fb')).toBe('fb')
    expect(() => { writeSaved('k', 1); writeRaw('k', 'x'); forgetKey('k') }).not.toThrow()
  })
})

describe('filed under who is logged in', () => {
  it('keeps two people apart on one browser', () => {
    writeRaw('settings', 'guest')
    data.set('profile', 'amina')
    expect(readRaw('settings')).toBe('')
    writeRaw('settings', 'amina')
    data.set('profile', 'bilal')
    expect(readRaw('settings')).toBe('')
    data.delete('profile')
    expect(readRaw('settings')).toBe('guest')
    expect(data.get('@amina/settings')).toBe('amina')
  })

  it('a shelf is one account\'s keys, bare, and fills whole', () => {
    data.set('@amina/a', '1')
    data.set('@bilal/b', '2')
    data.set('c', '3')
    data.set('profile', 'amina')
    expect(shelfOf('amina')).toEqual({ a: '1' })
    expect(shelfOf('')).toEqual({ c: '3' })
    fillShelf('amina', { z: '9' })
    expect(shelfOf('amina')).toEqual({ z: '9' })
    expect(shelfOf('bilal')).toEqual({ b: '2' })
  })

  it('tells listeners of every change, so the shelf can be sent', () => {
    const heard = vi.fn()
    const stop = onChange(heard)
    writeRaw('k', 'v')
    forgetKey('k')
    stop()
    writeRaw('k', 'v')
    expect(heard).toHaveBeenCalledTimes(2)
  })

  it('forgets one person\'s progress, not another\'s', () => {
    data.set('profile', 'amina')
    writeRaw(progressKey('grow'), '{}')
    data.set('@bilal/progress:grow', '{}')
    forgetProgressKeys()
    expect([...data.keys()]).toEqual(['profile', '@bilal/progress:grow'])
  })
})
