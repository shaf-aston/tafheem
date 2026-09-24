import { describe, expect, it } from 'vitest'

import { RECITERS, ayahAudioUrl } from './ayahAudio'

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
