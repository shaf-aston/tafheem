import { QueryClient } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

import { hadithOpen } from '../../api'
import { firstThese, load, onHover, warm } from './warm'

const query = (fn) => ({ queryKey: ['k'], queryFn: fn })

describe('warm', () => {
  it('prefetches once the page is idle', async () => {
    const fn = vi.fn().mockResolvedValue(1)
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
    warm(client, query(fn))
    expect(fn).not.toHaveBeenCalled()
    await vi.waitFor(() => expect(fn).toHaveBeenCalledTimes(1))
  })

  it('does not fetch what is already cached', async () => {
    const fn = vi.fn().mockResolvedValue(1)
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
    await client.prefetchQuery(query(fn))
    onHover(client, query(fn)).onPointerEnter()
    warm(client, query(fn))
    await new Promise((r) => setTimeout(r, 300))
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('load fetches its query once, however often it runs', async () => {
    const fn = vi.fn().mockResolvedValue(1)
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
    await load(query(fn))(client)
    await load(query(fn))(client)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('hadithOpen prefetches every collection\'s books', async () => {
    const keys = []
    const client = {
      fetchQuery: async () => [{ id: 'a' }, { id: 'b' }],
      prefetchQuery: (q) => keys.push(q.queryKey),
    }
    await hadithOpen(client)
    expect(keys).toEqual([['hadith-books', 'a'], ['hadith-books', 'b']])
  })
})

describe('idle and inTurn', () => {
  it('idle gives requestIdleCallback a deadline, so a busy page still warms', async () => {
    const { idle, IDLE_BY } = await import('./warm')
    const ric = vi.fn()
    vi.stubGlobal('requestIdleCallback', ric)
    const fn = () => {}
    idle(fn)
    expect(ric).toHaveBeenCalledWith(fn, { timeout: IDLE_BY })
    vi.unstubAllGlobals()
  })

  it('inTurn starts each step after the one before has finished, past failures', async () => {
    const { inTurn } = await import('./warm')
    const log = []
    let release
    const first = () => new Promise((r) => { release = r }).then(() => log.push('a'))
    const done = inTurn([first, () => { throw new Error('x') }, () => log.push('c')])
    await new Promise((r) => setTimeout(r, 10))
    expect(log).toEqual([])
    release()
    await done
    expect(log).toEqual(['a', 'c'])
  })
})

describe('firstThese', () => {
  it('moves the chosen ids to the front in their own order, keeping the rest in place', () => {
    expect(firstThese(['home', 'nahw', 'quran', 'dict', 'quiz'], ['quiz', 'home'])).toEqual(['quiz', 'home', 'nahw', 'quran', 'dict'])
  })

  it('ignores a chosen id that is not in the list', () => {
    expect(firstThese(['a', 'b'], ['gone', 'b'])).toEqual(['b', 'a'])
  })
})
