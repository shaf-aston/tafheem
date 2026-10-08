import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { copyGuestShelf, pullShelf } from './shelf'

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
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('the shelf on the server', () => {
  it('the server\'s copy wins on log-in', async () => {
    data.set('@amina/settings', 'old')
    vi.spyOn(api, 'get').mockResolvedValue({ data: { data: { settings: 'new' } } })
    await pullShelf('amina')
    expect([...data.entries()]).toEqual([['@amina/settings', 'new']])
  })

  it('a new account sends this device\'s copy up instead', async () => {
    data.set('@amina/settings', 'mine')
    vi.spyOn(api, 'get').mockResolvedValue({ data: { data: {} } })
    const put = vi.spyOn(api, 'put').mockResolvedValue({})
    await pullShelf('amina')
    expect(put.mock.calls[0][1]).toEqual({ data: { settings: 'mine' } })
  })

  it('offline, this device\'s copy stands and nothing throws', async () => {
    data.set('@amina/settings', 'mine')
    vi.spyOn(api, 'get').mockRejectedValue(new Error('Network Error'))
    await expect(pullShelf('amina')).resolves.toBeUndefined()
    expect(data.get('@amina/settings')).toBe('mine')
  })

  it('a sign-up that keeps the guest\'s answers keeps the guest\'s shelf', async () => {
    data.set('settings', 'guest')
    data.set('profile', 'amina')
    const put = vi.spyOn(api, 'put').mockResolvedValue({})
    await copyGuestShelf('amina')
    expect(data.get('@amina/settings')).toBe('guest')
    expect(put.mock.calls[0][1]).toEqual({ data: { settings: 'guest' } })
  })
})
