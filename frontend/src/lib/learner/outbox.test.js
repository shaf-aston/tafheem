import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import PROFILE from '../../config/profile.json'
import { forgetWaiting, hold, sendWaiting, waiting, worthRetrying } from './outbox'

const refused = (status) => Object.assign(new Error('refused'), { response: { status } })
const items = () => waiting().map((one) => one.body.item)

// A device's storage, as a Map: the tests run with no browser.
const memory = () => {
  const data = new Map()
  return { getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, String(v)), removeItem: (k) => data.delete(k) }
}

beforeEach(() => vi.stubGlobal('localStorage', memory()))
afterEach(() => vi.unstubAllGlobals())

describe('answers waiting for a signal', () => {
  it('keeps them oldest first, each with whose it is', () => {
    hold({ item: 'a' }, { who: 'amina' })
    hold({ item: 'b' }, { who: 'guest' })
    expect(waiting()).toEqual([{ body: { item: 'a' }, headers: { who: 'amina' } }, { body: { item: 'b' }, headers: { who: 'guest' } }])
  })

  it('keeps at most the configured number, dropping the oldest', () => {
    for (let i = 0; i < PROFILE.outbox.max + 2; i += 1) hold({ item: String(i) }, {})
    expect(waiting()).toHaveLength(PROFILE.outbox.max)
    expect(items()[0]).toBe('2')
  })

  it('forgets them all for Start over', () => {
    hold({ item: 'a' }, {})
    forgetWaiting()
    expect(waiting()).toEqual([])
  })

  it('reads a spoiled list as empty rather than breaking', () => {
    localStorage.setItem(PROFILE.outbox.key, '{not json')
    expect(waiting()).toEqual([])
  })

  it('retries only what no server judged: no signal, server down, too busy', () => {
    expect(worthRetrying(new Error('Network Error'))).toBe(true)
    expect(worthRetrying(refused(502))).toBe(true)
    expect(worthRetrying(refused(429))).toBe(true)
    expect(worthRetrying(refused(422))).toBe(false)
    expect(worthRetrying(refused(403))).toBe(false)
  })
})

describe('sending them', () => {
  it('sends in order, with the header they were kept with, and empties the list', async () => {
    hold({ item: 'a' }, { who: 'amina' })
    hold({ item: 'b' }, { who: 'amina' })
    const post = vi.fn().mockResolvedValue({})
    await expect(sendWaiting(post)).resolves.toBe(2)
    expect(post.mock.calls).toEqual([[{ item: 'a' }, { who: 'amina' }], [{ item: 'b' }, { who: 'amina' }]])
    expect(waiting()).toEqual([])
  })

  it('stops at the first that still cannot land, keeping it and the rest', async () => {
    hold({ item: 'a' }, {})
    hold({ item: 'b' }, {})
    const post = vi.fn().mockRejectedValue(new Error('Network Error'))
    await expect(sendWaiting(post)).resolves.toBe(0)
    expect(post).toHaveBeenCalledTimes(1)
    expect(items()).toEqual(['a', 'b'])
  })

  it('drops one the server refuses and goes on', async () => {
    hold({ item: 'bad' }, {})
    hold({ item: 'good' }, {})
    const post = vi.fn().mockRejectedValueOnce(refused(422)).mockResolvedValue({})
    await expect(sendWaiting(post)).resolves.toBe(1)
    expect(waiting()).toEqual([])
  })

  it('keeps an answer held while sending, and sends it in the same run', async () => {
    hold({ item: 'a' }, {})
    const post = vi.fn().mockImplementation(async (body) => {
      if (body.item === 'a') hold({ item: 'late' }, {})
    })
    await expect(sendWaiting(post)).resolves.toBe(2)
    expect(post.mock.calls.map(([body]) => body.item)).toEqual(['a', 'late'])
  })

  it('runs once at a time: a second call shares the first run', async () => {
    hold({ item: 'a' }, {})
    const post = vi.fn().mockResolvedValue({})
    const [one, two] = [sendWaiting(post), sendWaiting(post)]
    expect(await one).toBe(1)
    expect(await two).toBe(1)
    expect(post).toHaveBeenCalledTimes(1)
  })
})
