import { afterEach, describe, expect, it, vi } from 'vitest'

import { localHears } from './ears-local'

describe('localHears', () => {
  afterEach(() => { vi.unstubAllGlobals() })

  it('posts the recording to the backend with match forced and no fusha hint', async () => {
    const fetchMock = vi.fn(async (url, init) => {
      expect(url).toBe('http://127.0.0.1:8011/api/listen?match=true&fusha=false')
      expect(init.method).toBe('POST')
      expect(init.body).toBeInstanceOf(FormData)
      expect(init.body.get('audio')).toBeInstanceOf(Blob)
      return { ok: true, json: async () => ({ text: 'بسم الله' }) }
    })
    vi.stubGlobal('fetch', fetchMock)

    const said = await localHears('http://127.0.0.1:8011/api/listen')(Buffer.from([1, 2, 3]))

    expect(said).toBe('بسم الله')
    expect(fetchMock).toHaveBeenCalledOnce()
  })

  it('throws with the backend detail when the response is not ok', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: false,
      json: async () => ({ detail: 'not installed' }),
    })))

    await expect(localHears('http://127.0.0.1:8011/api/listen')(Buffer.from([1])))
      .rejects.toThrow('not installed')
  })
})
