import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getProfile, logInAs, logOut, profileHeaders } from './profile'

describe('profileHeaders', () => {
  beforeEach(() => {
    const data = new Map()
    vi.stubGlobal('localStorage', {
      getItem: (k) => (data.has(k) ? data.get(k) : null),
      setItem: (k, v) => data.set(k, String(v)),
    })
    vi.stubGlobal('location', { reload: vi.fn() })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends this device\'s guest id before a name is kept', () => {
    expect(profileHeaders()).toEqual({ 'X-Tafheem-Guest': expect.stringMatching(/^[0-9a-f]{32}$/) })
  })

  it('sends the kept name, encoded so Arabic survives a header', () => {
    logInAs('عائشة')
    expect(getProfile()).toBe('عائشة')
    expect(profileHeaders()).toEqual({ 'X-Tafheem-Profile': encodeURIComponent('عائشة') })
  })

  it('sends a name being tried before it is kept', () => {
    expect(profileHeaders(' Amina ')).toEqual({ 'X-Tafheem-Profile': '%20Amina%20' })
  })
})

it('logging out goes back to the guest record, reloaded', () => {
  const data = new Map([['profile', 'amina']])
  vi.stubGlobal('localStorage', { getItem: (k) => data.get(k) ?? null, removeItem: (k) => data.delete(k) })
  vi.stubGlobal('location', { reload: vi.fn() })
  logOut()
  expect(Object.keys(profileHeaders())).toEqual(['X-Tafheem-Guest'])
  expect(location.reload).toHaveBeenCalledOnce()
  vi.unstubAllGlobals()
})

describe('deviceId', () => {
  let data
  // A fresh copy of the module each time: the id held for a visit must not leak from one test to the next.
  const load = async () => {
    vi.resetModules()
    return import('./profile')
  }
  beforeEach(() => {
    data = new Map()
    vi.stubGlobal('localStorage', { getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, String(v)) })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('is 128 random bits as 32 lowercase hex, made once and kept under "guest"', async () => {
    vi.stubGlobal('crypto', { getRandomValues: (bytes) => bytes.map((_, i) => i * 17) })
    const { deviceId } = await load()
    expect(deviceId()).toBe('00112233445566778899aabbccddeeff')
    vi.stubGlobal('crypto', { getRandomValues: (bytes) => bytes.fill(255) })
    expect(deviceId()).toBe('00112233445566778899aabbccddeeff')
    expect(data.get('guest')).toBe('00112233445566778899aabbccddeeff')
  })

  it('reads back the id the device already holds', async () => {
    data.set('guest', 'ab'.repeat(16))
    const { deviceId, profileHeaders } = await load()
    expect(deviceId()).toBe('ab'.repeat(16))
    expect(profileHeaders('')).toEqual({ 'X-Tafheem-Guest': 'ab'.repeat(16) })
  })

  it.each(['', 'nope', 'AB'.repeat(16), 'a'.repeat(31), 'a'.repeat(33)])('replaces a kept id the server would refuse: %j', async (bad) => {
    data.set('guest', bad)
    const { deviceId } = await load()
    const made = deviceId()
    expect(made).toMatch(/^[0-9a-f]{32}$/)
    expect(data.get('guest')).toBe(made)
  })

  it('holds one id for the visit when storage throws', async () => {
    const boom = () => { throw new Error('blocked') }
    vi.stubGlobal('localStorage', { getItem: boom, setItem: boom })
    const { deviceId } = await load()
    const first = deviceId()
    expect(first).toMatch(/^[0-9a-f]{32}$/)
    expect(deviceId()).toBe(first)
  })

  it('a logged-in name sends only the name, never the device', async () => {
    data.set('profile', 'amina')
    const { profileHeaders } = await load()
    expect(profileHeaders()).toEqual({ 'X-Tafheem-Profile': 'amina' })
  })
})
