import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { cleanName, getProfile, profileHeaders, setProfile } from './profile'

describe('cleanName', () => {
  it.each([
    [' Amina ', 'amina'],
    ['AMINA', 'amina'],
    ['a  b', 'a b'],
    ['عائشة', 'عائشة'],
    ['عَائِشَة', 'عَائِشَة'],
    ['Amina-2_b.c', 'amina-2_b.c'],
    ['x'.repeat(40), 'x'.repeat(40)],
  ])('%s is %s', (raw, clean) => {
    expect(cleanName(raw)).toEqual({ name: clean })
  })

  it.each(['', '   ', 'x'.repeat(41), '<x>', 'a/b', 'local', ' LOCAL '])('refuses %j', (raw) => {
    expect(cleanName(raw).error).toBeTruthy()
  })
})

describe('profileHeaders', () => {
  beforeEach(() => {
    const data = new Map()
    vi.stubGlobal('localStorage', {
      getItem: (k) => (data.has(k) ? data.get(k) : null),
      setItem: (k, v) => data.set(k, String(v)),
      removeItem: (k) => data.delete(k),
    })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends nothing before a name is typed', () => {
    expect(profileHeaders()).toEqual({})
  })

  it('sends the saved name, encoded so Arabic survives a header', () => {
    setProfile('عائشة')
    expect(getProfile()).toBe('عائشة')
    expect(profileHeaders()).toEqual({ 'X-Tafheem-Profile': encodeURIComponent('عائشة') })
  })

  it('forgets the name when cleared', () => {
    setProfile('amina')
    setProfile('')
    expect(profileHeaders()).toEqual({})
  })
})
