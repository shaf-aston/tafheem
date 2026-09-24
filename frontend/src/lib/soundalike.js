/**
 * One question: are these two different words that a microphone would confuse?
 *
 * It is the orange rule. When somebody recites ٱلصِّرَٰطَ and ٱلسِّرَاط comes back, two
 * things could have happened and nothing in the text says which: they said the
 * wrong word, or the engine misheard the right one. Orange is the app admitting
 * that, the same way the rest of it separates what is verified from what is
 * guessed. Red is only for a word that could not have been misheard.
 *
 * The order matters and is enforced here rather than asked of every caller:
 * spelling is folded first by arabicText, and only what is left over reaches the
 * sound fold. مَٰلِكِ against مالك is one word, not a near miss, and this function
 * answers false for it because sameSpokenWord answers true.
 *
 * Pure. No React, no microphone, no network: every hard case is two strings.
 */
import config from '../recite.json'
import { recitedForms, sameSpokenWord } from './arabicText'

// Every letter in a group becomes the group's first letter, so the whole group
// compares as one sound. Built once: the groups never change while running.
const SOUND_OF = new Map(
  config['sound-alike-groups'].flatMap((group) => [...group].map((letter) => [letter, group[0]])),
)

const KEEPS_AT_LEAST = config['article-keeps-at-least']

/** The word without its ال, when there is enough word left to still be one. */
const withoutArticle = (form) =>
  form.startsWith('ال') && form.length - 2 >= KEEPS_AT_LEAST ? form.slice(2) : form

/**
 * A word reduced to the sounds a microphone can tell apart. Not a spelling, and
 * never shown to anyone: two different words can share one of these.
 */
export const soundFold = (form) =>
  [...withoutArticle(form)].map((letter) => SOUND_OF.get(letter) ?? letter).join('')

/**
 * True when `heard` and `printed` are different words that sound the same.
 *
 * False when they are the same word however it is written, and false when they
 * are far enough apart to say so plainly. Both are what the caller wants: this
 * is asked once per word and its answer is the colour.
 */
export const soundsTheSame = (heard, printed) => {
  if (!heard || !printed) return false
  if (sameSpokenWord(heard, printed)) return false

  const theirs = new Set([...recitedForms(printed)].map(soundFold))
  return [...recitedForms(heard)]
    .map(soundFold)
    .some((form) => form !== '' && theirs.has(form))
}
