import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryClient } from './queryClient'
import { loadStatic, staticQuery } from './staticQuery'

const answer = (status, body) => vi.fn(async () => ({ ok: status < 400, status, json: async () => body }))

beforeEach(() => {
  queryClient.clear()
  vi.unstubAllGlobals()
})

describe('staticQuery', () => {
  it('fetches a file once and then answers from the cache', async () => {
    const fetch = answer(200, { words: [1, 2] })
    vi.stubGlobal('fetch', fetch)
    expect(await loadStatic('/words/words.json', 'the words')).toEqual({ words: [1, 2] })
    expect(await queryClient.fetchQuery(staticQuery('/words/words.json', 'the words'))).toEqual({ words: [1, 2] })
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('says what could not be loaded and with which status, and does not cache the failure', async () => {
    vi.stubGlobal('fetch', answer(404))
    await expect(loadStatic('/a.json', 'the book')).rejects.toThrow('Could not load the book (404)')
    const fetch = answer(200, { ok: true })
    vi.stubGlobal('fetch', fetch)
    expect(await loadStatic('/a.json', 'the book')).toEqual({ ok: true })
  })
})
