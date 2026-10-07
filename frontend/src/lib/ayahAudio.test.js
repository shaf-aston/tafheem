import { afterEach, describe, expect, it, vi } from 'vitest'

import { RECITERS, ayahAudioUrl, nowPlaying, play, reset, watchEnd } from './ayahAudio'

describe('where an ayah\u2019s recording lives', () => {
  it('pads both numbers to three digits, which is the file naming', () => {
    expect(ayahAudioUrl(2, 255, 'alafasy')).toBe(
      'https://everyayah.com/data/Alafasy_128kbps/002255.mp3',
    )
  })

  it('pads a one-digit surah and a one-digit ayah too', () => {
    expect(ayahAudioUrl(1, 1, 'alafasy')).toContain('/001001.mp3')
  })

  it('handles the last ayah of the longest surah', () => {
    expect(ayahAudioUrl(114, 6, 'husary')).toBe(
      'https://everyayah.com/data/Husary_128kbps/114006.mp3',
    )
  })

  it('falls back to the first reciter rather than a broken address', () => {
    // A remembered choice outlives the list it came from. An unknown one must
    // play something, never build a url with "undefined" in it.
    expect(ayahAudioUrl(2, 255, 'someone-who-left')).toBe(ayahAudioUrl(2, 255, RECITERS[0].id))
    expect(ayahAudioUrl(2, 255, '')).not.toContain('undefined')
  })

  it('names every reciter fully, since the picker shows these', () => {
    for (const one of RECITERS) {
      expect(one.id).toBeTruthy()
      expect(one.name).toBeTruthy()
      expect(one.folder).toBeTruthy()
    }
    expect(new Set(RECITERS.map((one) => one.id)).size).toBe(RECITERS.length)
  })
})

describe('hearing that a recording finished', () => {
  // Enough of an <audio> element to fire its events: a browser fires 'pause'
  // just before 'ended', which is what used to empty the url by then.
  class FakeAudio extends EventTarget {
    paused = true
    ended = false
    load() {}
    play() { this.paused = false; this.dispatchEvent(new Event('play')); return Promise.resolve() }
    pause() { this.paused = true; this.dispatchEvent(new Event('pause')) }
    finish() { this.ended = true; this.pause(); this.dispatchEvent(new Event('ended')) }
  }
  afterEach(() => { reset(); vi.unstubAllGlobals() })

  it('names the recording that played to its end, and not one stopped early', async () => {
    let element
    vi.stubGlobal('Audio', class extends FakeAudio { constructor() { super(); element = this } })
    const heard = []
    watchEnd((url) => heard.push(url))

    await play('https://x/001001.mp3')
    element.pause()
    expect(heard).toEqual([])

    await play('https://x/001002.mp3')
    element.finish()
    expect(heard).toEqual(['https://x/001002.mp3'])
    expect(nowPlaying()).toBe('')
  })
})
