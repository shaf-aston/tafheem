import { afterEach, describe, expect, it, vi } from 'vitest'

import config from '../../config/rewards.json'
import { announce, onEarned, rankOf, shareOf, tz } from './rewards'

describe('rankOf', () => {
  it('names a level by the highest rank it has reached', () => {
    expect(rankOf(1).en).toBe('Seed')
    expect(rankOf(3).en).toBe('Sprout')
    expect(rankOf(4).en).toBe('Branch')
    expect(rankOf(40).en).toBe('Fruit')
  })

  it('keeps the ranks in rising order, so findLast is right', () => {
    const starts = config.ranks.map((rank) => rank.from)
    expect(starts).toEqual([...starts].sort((a, b) => a - b))
    expect(starts[0]).toBe(1)
  })
})

describe('shareOf', () => {
  it('is how far through the level', () => {
    expect(shareOf({ into: 50, need: 200 })).toBe(0.25)
    expect(shareOf({ into: 0, need: 0 })).toBe(0)
  })
})

describe('tz', () => {
  it('is minutes east of UTC', () => {
    const now = { getTimezoneOffset: () => -60 }
    expect(tz(now)).toBe(60)
    expect(tz({ getTimezoneOffset: () => 0 })).toBe(0)
  })
})

describe('announce', () => {
  let stop
  afterEach(() => stop?.())

  it('tells listeners about an answer that came back with rewards', () => {
    const heard = vi.fn()
    stop = onEarned(heard)
    announce({ earned: 10, rewards: { xp: 10 } })
    expect(heard).toHaveBeenCalledWith({ earned: 10, rewards: { xp: 10 } })
  })

  it('says nothing for the guest record, which has none', () => {
    const heard = vi.fn()
    stop = onEarned(heard)
    announce({ earned: 0, rewards: null })
    announce(undefined)
    expect(heard).not.toHaveBeenCalled()
  })

  it('stops telling once unsubscribed', () => {
    const heard = vi.fn()
    onEarned(heard)()
    announce({ earned: 10, rewards: { xp: 10 } })
    expect(heard).not.toHaveBeenCalled()
  })
})
