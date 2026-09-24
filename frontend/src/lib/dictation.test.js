import { describe, expect, it } from 'vitest'
import config from '../dictation.json'
import { freshSamples, isVoice, quietLimitMs } from './dictation'

describe('when a recording stops itself', () => {
  it('ends soon after a voice stops', () => {
    expect(quietLimitMs(true)).toBe(config['after-speech-s'] * 1000)
    expect(quietLimitMs(true)).toBeLessThan(2000)
  })

  // The case nobody asks for: nothing said yet. Cutting that off is worse
  // than waiting, so it keeps the long limit.
  it('a patient listener waits the long time even after a voice', () => {
    // Reciting: the page ended the whole recitation at the first breath
    // between ayahs, a 0.75 second pause inside 1:7 as Alafasy reads it.
    expect(quietLimitMs(true, true)).toBe(config['quiet-stop-s'] * 1000)
  })

  it('waits far longer when no voice has been heard', () => {
    expect(quietLimitMs(false)).toBe(config['quiet-stop-s'] * 1000)
    expect(quietLimitMs(false)).toBeGreaterThan(quietLimitMs(true) * 5)
  })

  it('counts speech as a voice and room noise as silence', () => {
    expect(isVoice(0.1)).toBe(true)
    expect(isVoice(0.002)).toBe(false)
  })

  // The bug this rule exists for: someone reciting softly measured under the
  // old fixed level, so nothing they said was ever counted as a voice, nothing
  // was ever sent to be read, and the page said they had recited nothing.
  it('hears a quiet reciter, so long as they stand above their own room', () => {
    const room = 0.004
    expect(isVoice(0.03, room)).toBe(true)
    expect(isVoice(0.015, room)).toBe(true)
  })

  it('does not hear a hissy room as a voice', () => {
    const hissy = 0.03
    expect(isVoice(0.05, hissy)).toBe(false)
    expect(isVoice(0.2, hissy)).toBe(true)
  })

  // A microphone reporting a perfectly silent room would otherwise make every
  // faint number many times the room, and so a voice.
  it('keeps a floor under it however silent the room measures', () => {
    expect(isVoice(config['voice-level'] / 2, 0)).toBe(false)
    expect(isVoice(config['voice-level'] * 2, 0)).toBe(true)
  })
})

describe('how much of the meter one read judges', () => {
  const perRead = (rate) => rate * config['level-check-ms'] / 1000

  it('covers judge-s of sound, and never less than the time since the last read', () => {
    for (const rate of [44100, 48000]) {
      const got = freshSamples(rate, 1e9)
      expect(got).toBeGreaterThan(perRead(rate))
      expect(got).toBeGreaterThanOrEqual(rate * config['judge-s'])
      expect(got).toBeLessThanOrEqual(Math.ceil(rate * Math.max(config['judge-s'], perRead(1) * 1.5)))
    }
  })

  it('never asks for more than the meter holds', () => {
    expect(freshSamples(48000, 2048)).toBe(2048)
    expect(freshSamples(48000, 32768)).toBeLessThanOrEqual(32768)
  })
})
