import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getProfile, logOut, profileHeaders, setProfile } from './profile'

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
    setProfile('عائشة', 'k1')
    expect(getProfile()).toBe('عائشة')
    expect(profileHeaders()).toEqual({
      'X-Tafheem-Profile': encodeURIComponent('عائشة'), 'X-Tafheem-Key': 'k1',
    })
  })

  it('sends the key only with the signed-in name, never with one being tried', () => {
    setProfile('amina', 'k1')
    expect(profileHeaders('bilal')).toEqual({ 'X-Tafheem-Profile': 'bilal' })
  })

  it('sends a name being tried before it is kept', () => {
    expect(profileHeaders(' Amina ')).toEqual({ 'X-Tafheem-Profile': '%20Amina%20' })
  })
})

it('logging out goes back to the guest record', () => {
  const data = new Map([['profile', 'amina'], ['profile-key', 'k1']])
  vi.stubGlobal('localStorage', { getItem: (k) => data.get(k) ?? null, removeItem: (k) => data.delete(k) })
  logOut()
  expect(profileHeaders()).toEqual({})
  expect(data.size).toBe(0)
  vi.unstubAllGlobals()
})
