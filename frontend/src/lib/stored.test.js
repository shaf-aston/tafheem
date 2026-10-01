import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { forgetKey, readRaw, readSaved, writeRaw, writeSaved } from './stored'

let data
beforeEach(() => {
  data = new Map()
  vi.stubGlobal('localStorage', {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: (k) => data.delete(k),
  })
})
afterEach(() => vi.unstubAllGlobals())

describe('stored', () => {
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
