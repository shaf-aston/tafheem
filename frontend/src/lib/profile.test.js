import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getProfile, logOut, profileHeaders, readsProgress, setProfile } from './profile'

describe('profileHeaders', () => {
  beforeEach(() => {
    const data = new Map()
    vi.stubGlobal('localStorage', {
      getItem: (k) => (data.has(k) ? data.get(k) : null),
      setItem: (k, v) => data.set(k, String(v)),
    })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends nothing before a name is kept', () => {
    expect(profileHeaders()).toEqual({})
  })

  it('sends the kept name, encoded so Arabic survives a header', () => {
    setProfile('عائشة')
    expect(getProfile()).toBe('عائشة')
    expect(profileHeaders()).toEqual({ 'X-Tafheem-Profile': encodeURIComponent('عائشة') })
  })

  it('sends a name being tried before it is kept', () => {
    expect(profileHeaders(' Amina ')).toEqual({ 'X-Tafheem-Profile': '%20Amina%20' })
  })
})

it('refetches only queries that read progress', () => {
  expect(readsProgress({ queryKey: ['quiz-review', 'en'] })).toBe(true)
  expect(readsProgress({ queryKey: ['quran-surah', 1] })).toBe(false)
})

it('logging out goes back to the guest record', () => {
  const data = new Map([['profile', 'amina']])
  vi.stubGlobal('localStorage', { getItem: (k) => data.get(k) ?? null, removeItem: (k) => data.delete(k) })
  logOut()
  expect(profileHeaders()).toEqual({})
  vi.unstubAllGlobals()
})
