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

const { prepare, speak, reset, pickVoice, speedFor } = await import('./speak')

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

  it('asks a dialect\'s own speaker, never a reciter, when given an accent', async () => {
    const voice = await speak('كِتَاب', { accent: 'damascene' })
    expect(voice.id).toBe('server')
    expect(played).toEqual([`/api/speak?text=${encodeURIComponent('كِتَاب')}&voice=${config.voices.server.version}&accent=damascene`])
  })

  it('says a word pressed again soon after slower, like a teacher repeating it', async () => {
    await speak('قَطَاة')
    await speak('قَطَاة')
    expect(played[1]).toContain(`&speed=${config.repeatSpeed}`)
    expect(played[0]).not.toContain('speed=')
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

describe('the speed of a press', () => {
  it('is the setting, unless the same word was pressed within repeatMs', () => {
    expect(speedFor('أُمَّة', 0, 'normal')).toBe('normal')
    expect(speedFor('أُمَّة', config.repeatMs - 1, 'normal')).toBe(config.repeatSpeed)
    expect(speedFor('أُمَّة', 3 * config.repeatMs, 'normal')).toBe('normal')
    expect(speedFor('فِتْنَة', 3 * config.repeatMs + 1, 'slow')).toBe('slow')
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

  it('readies a phrase once per accent, so a second dialect still gets its own voice', async () => {
    await prepare('كِيفَك', { accent: 'damascene' })
    await prepare('كِيفَك', { accent: 'damascene' })
    await prepare('كِيفَك', { accent: 'lebanese' })
    const asked = globalThis.fetch.mock.calls.map(([url]) => url).filter((url) => url.startsWith('/api/speak'))
    expect(asked.map((url) => new URL(url, 'http://x').searchParams.get('accent'))).toEqual(['damascene', 'lebanese'])
  })

  it('marks the ask as ahead, so a word pressed on the server goes first', async () => {
    await prepare('بَابٌ مَفْتُوحٌ')
    const [, options] = globalThis.fetch.mock.calls.find(([url]) => url.startsWith('/api/speak'))
    expect(options.headers['X-Speak-Ahead']).toBe('1')
  })
})

const voice = (name, lang, localService = true) => ({ name, lang, localService })

describe('choosing a device voice', () => {
  it('prefers a named voice over another Arabic one', () => {
    const voices = [voice('Other', 'ar-SA'), voice('Majed', 'ar_EG', false)]
    expect(pickVoice(voices, config).name).toBe('Majed')
  })

  it('prefers a local Arabic voice over a remote one when none is named', () => {
    const voices = [voice('Remote', 'ar-SA', false), voice('Local', 'AR', true)]
    expect(pickVoice(voices, config).name).toBe('Local')
  })

  it('gives nothing when only English voices exist', () => {
    expect(pickVoice([voice('Samantha', 'en-US'), voice('Daniel', 'en-GB')], config)).toBeNull()
  })
})

describe('the device voice', () => {
  let synth
  beforeEach(() => {
    refuse = () => true  // recorded and server fail, so the device voice is reached
    synth = {
      voices: [],
      listeners: [],
      getVoices() { return this.voices },
      addEventListener(_, fn) { this.listeners.push(fn) },
      removeEventListener() {},
      cancel: vi.fn(),
      speak: vi.fn((line) => queueMicrotask(() => line.onstart())),
    }
    globalThis.speechSynthesis = synth
    globalThis.SpeechSynthesisUtterance = class { constructor(text) { this.text = text } }
  })

  it('refuses, and never speaks, when the device has no Arabic voice', async () => {
    synth.voices = [voice('Samantha', 'en-US')]
    await expect(speak('قِطَار')).rejects.toThrow('No voice could say this')
    expect(synth.speak).not.toHaveBeenCalled()
  })

  it('waits for the voice list, then speaks with the Arabic voice', async () => {
    const arabic = voice('Hoda', 'ar-EG')
    const pending = speak('قِطَار')
    await vi.waitFor(() => expect(synth.listeners).toHaveLength(1))
    synth.voices = [voice('Samantha', 'en-US'), arabic]
    synth.listeners[0]()
    expect((await pending).id).toBe('browser')
    expect(synth.speak.mock.calls[0][0].voice).toBe(arabic)
    expect(synth.speak.mock.calls[0][0].lang).toBe('ar-EG')
  })
})
