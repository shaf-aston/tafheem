import { describe, expect, it } from 'vitest'

import config from '../recite.json'
import { soundFold, soundsTheSame } from './soundalike'

describe('a word written two ways is never a near miss', () => {
  // The mistake this whole feature has to not make. The Qur'an writes the long
  // a as a small standing alef and everyone else writes a full one; they are
  // one word, so the orange rule must not even be reached.
  it('does not fire on the standing alef', () => {
    expect(soundsTheSame('مالك', 'مَٰلِكِ')).toBe(false)
    expect(soundsTheSame('الرحمن', 'ٱلرَّحْمَٰنِ')).toBe(false)
    expect(soundsTheSame('الرحمان', 'ٱلرَّحْمَٰنِ')).toBe(false)
  })

  it('does not fire on the wasla alef, the maqsura, or bare vowels', () => {
    expect(soundsTheSame('الله', 'ٱللَّهِ')).toBe(false)
    expect(soundsTheSame('علي', 'عَلَىٰ')).toBe(false)
    expect(soundsTheSame('الحمد', 'ٱلْحَمْدُ')).toBe(false)
  })
})

describe('two different words a microphone confuses', () => {
  it('hears the emphatic s as a plain one', () => {
    expect(soundsTheSame('ٱلسِّرَاط', 'ٱلصِّرَٰطَ')).toBe(true)
  })

  it('hears the emphatic d as a th', () => {
    expect(soundsTheSame('ٱلظَّالِّينَ', 'ٱلضَّآلِّينَ')).toBe(true)
  })

  it('swaps t for the emphatic t, and k for q', () => {
    expect(soundsTheSame('تين', 'طين')).toBe(true)
    expect(soundsTheSame('كلب', 'قلب')).toBe(true)
  })

  it('cannot tell the breath at the end of a word', () => {
    expect(soundsTheSame('رحمه', 'رحمة')).toBe(true)
  })

  it('loses the ال at the front, which a cut in the sound does', () => {
    // Really heard: Groq returned رحمن for ٱلرَّحْمَٰنِ where a window ended.
    expect(soundsTheSame('رحمن', 'ٱلرَّحْمَٰنِ')).toBe(true)
    expect(soundsTheSame('صراط', 'ٱلصِّرَٰطَ')).toBe(true)
  })

  it('keeps the ال when dropping it would leave a word somebody might mean', () => {
    // لله is a word in its own right, and reciting it where ٱللَّهِ belongs is a
    // real mistake, not a mishearing.
    expect(soundsTheSame('لله', 'ٱللَّهِ')).toBe(false)
  })
})

describe('a word that is plainly a different word', () => {
  it('says so for a word with letters missing', () => {
    // Really heard on this machine: أنعمت came back as أنت.
    expect(soundsTheSame('أنت', 'أَنْعَمْتَ')).toBe(false)
  })

  it('says so for a different word of the same length', () => {
    expect(soundsTheSame('وَمَا', 'وَلَا')).toBe(false)
    expect(soundsTheSame('كتاب', 'حساب')).toBe(false)
  })

  it('says so when the engine wrote something else entirely', () => {
    expect(soundsTheSame('المرضوب', 'ٱلْمَغْضُوبِ')).toBe(false)
  })
})

describe('nothing to compare', () => {
  it('is not a near miss', () => {
    expect(soundsTheSame('', 'الله')).toBe(false)
    expect(soundsTheSame('الله', '')).toBe(false)
    expect(soundsTheSame(undefined, 'الله')).toBe(false)
    // A word of marks alone folds to nothing, and nothing must not match
    // everything: an empty fold on both sides is still not a near miss.
    expect(soundsTheSame('ً', 'ٍ')).toBe(false)
  })
})

describe('the fold itself', () => {
  it('sends every letter of a group to the same letter', () => {
    expect(soundFold('سصث')).toBe('سسس')
    expect(soundFold('دضظذز')).toBe('ددددد')
  })

  it('leaves a letter in no group alone', () => {
    expect(soundFold('كتب')).toBe('قتب')
    expect(soundFold('لم')).toBe('لم')
  })
})

describe('the settings in recite.json', () => {
  it('never puts one letter in two groups, which would make the fold undefined', () => {
    const seen = new Set()
    for (const group of config['sound-alike-groups']) {
      for (const letter of group) {
        expect(seen.has(letter), `${letter} is in two groups`).toBe(false)
        seen.add(letter)
      }
    }
  })

  it('waits for whole words, not a fraction of one, before marking', () => {
    expect(Number.isInteger(config['settle-words'])).toBe(true)
    expect(config['settle-words']).toBeGreaterThan(0)
  })

  it('moves the window often enough to stay under 20 requests a minute', () => {
    expect(60 / config['step-s']).toBeLessThanOrEqual(20)
    expect(config['step-s']).toBeLessThanOrEqual(config['window-s'])
  })

  it('leaves the allowance, and not the floor between two readings, in charge of the pacing', () => {
    // Under the ear's own twenty a minute, with room for the readings at each
    // pause, which never wait; and the floor is loose enough that a reciter
    // can actually reach the allowance rather than the floor stopping them first.
    expect(Number.isInteger(config['asks-per-minute'])).toBe(true)
    expect(config['asks-per-minute']).toBeLessThan(20)
    expect(60 / config['step-s']).toBeGreaterThanOrEqual(config['asks-per-minute'])
  })

  it('hands sound over more often than it asks for a reading', () => {
    expect(config['tick-s']).toBeGreaterThan(0)
    expect(config['tick-s']).toBeLessThanOrEqual(config['step-s'])
  })
})
