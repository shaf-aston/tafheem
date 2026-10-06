import { beforeEach, describe, expect, it, vi } from 'vitest'

import config from '../speak.json'

const played = []
let refuse = () => false
let tell = null
vi.mock('./ayahAudio', () => ({
  play: vi.fn(async (url) => {
    played.push(url)
    if (refuse(url)) throw new Error('would not load')
  }),
  stop: vi.fn(),
  watch: vi.fn((fn) => { tell = fn; return () => {} }),
}))

const { prepare, speak, reset } = await import('./speak')

beforeEach(() => {
  played.length = 0
  refuse = () => false
  reset()
  globalThis.fetch = vi.fn(async () => ({ ok: true, json: async () => ({ 'كِتَاب': 'wbw/002_002_002.mp3' }) }))
})

describe('which voice says a word', () => {
  it('uses the reciter when the word has a recording', async () => {
    const voice = await speak('كِتَاب')
    expect(voice.id).toBe('recorded')
    expect(played).toEqual(['https://audio.qurancdn.com/wbw/002_002_002.mp3'])
  })

  it('passes a word with no recording to the server voice', async () => {
    const voice = await speak('قِطَار')
    expect(voice.id).toBe('server')
    // The voice's version rides along, so a browser never replays a word kept from an older voice.
    expect(played[0]).toBe(`/api/speak?text=${encodeURIComponent('قِطَار')}&voice=${config.voices.server.version}`)
  })

  it('falls through to the next voice when a file will not load', async () => {
    refuse = (url) => url.includes('qurancdn')
    const voice = await speak('كِتَاب')
    expect(voice.id).toBe('server')
  })

  it('still speaks when the recording map cannot be fetched', async () => {
    globalThis.fetch = vi.fn(async () => { throw new Error('offline') })
    expect((await speak('كِتَاب')).id).toBe('server')
  })

  it('fails loud when no voice at all can say it', async () => {
    refuse = () => true
    await expect(speak('قِطَار')).rejects.toThrow('No voice')
  })

  it('asks for the recording map again after a failed fetch', async () => {
    globalThis.fetch = vi.fn(async () => ({ ok: false, status: 503 }))
    expect((await speak('كِتَاب')).id).toBe('server')
    globalThis.fetch = vi.fn(async () => ({ ok: true, json: async () => ({ 'كِتَاب': 'wbw/002_002_002.mp3' }) }))
    expect((await speak('كِتَاب')).id).toBe('recorded')
  })

  it('never mistakes an inherited name for a recording', async () => {
    expect((await speak('constructor')).id).toBe('server')
  })

  it('stops, not falls through, when a newer press cuts it off', async () => {
    let release
    refuse = (url) => url.includes('/api/speak')
    const { play } = await import('./ayahAudio')
    play.mockImplementationOnce((url) => new Promise((_, reject) => {
      played.push(url)
      release = () => reject(new Error('aborted'))
    }))
    const older = speak('قِطَار')       // server voice, still loading
    await vi.waitFor(() => expect(release).toBeTypeOf('function'))
    refuse = () => false
    const newer = speak('كِتَاب')
    release()
    await expect(older).rejects.toMatchObject({ interrupted: true })
    expect((await newer).id).toBe('recorded')
    expect(played.filter((u) => u.includes('/api/speak'))).toHaveLength(1)
  })

  it('says done once the player moves on', async () => {
    const voice = await speak('كِتَاب')
    let finished = false
    voice.done.then(() => { finished = true })
    tell('')
    await voice.done
    expect(finished).toBe(true)
  })
})

describe('readying a voice before the press', () => {
  it('asks the server once for a phrase with no recording, never for a recorded word', async () => {
    await prepare('كِتَاب')
    await prepare('بَيْتٌ كَبِيرٌ')
    await prepare('بَيْتٌ كَبِيرٌ')
    const asked = globalThis.fetch.mock.calls.map(([url]) => url).filter((url) => url.startsWith('/api/speak'))
    expect(asked).toEqual([`/api/speak?text=${encodeURIComponent('بَيْتٌ كَبِيرٌ')}&voice=${config.voices.server.version}`])
  })
})
