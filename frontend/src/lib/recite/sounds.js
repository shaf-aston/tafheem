/** The sounds ear's symbols written back as Arabic, for the word card. Pure. */
import config from '../../config/recite.json'

const LETTERS = config['sound-letters']
const VOWELS = config['sound-vowels']
const SHADDA = 'ّ'

/** One symbol as Arabic: a vowel, a letter, or a doubled letter (bb, dˤdˤ) with a shadda. */
const written = (sound) => {
  if (VOWELS[sound]) return VOWELS[sound]
  if (LETTERS[sound]) return LETTERS[sound]
  const half = sound.slice(0, sound.length / 2)
  return sound.length % 2 === 0 && half + half === sound && LETTERS[half] ? LETTERS[half] + SHADDA : ''
}

/** A word's sounds, ['q','u','l'], as Arabic, "قُل". Unknown symbols are dropped. */
export const asArabic = (sounds = []) => sounds.map(written).join('')
