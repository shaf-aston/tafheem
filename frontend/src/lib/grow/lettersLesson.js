/**
 * Letters world cards: the 28 letters (public/grow/letters.json), for one who cannot read Arabic yet, before the Basics.
 * Per letter: a teach card (the letter, its name and sound, how it joins), "which one is bā’?" among letters of its own
 * shape (they differ only by their dots, so that is where the eye must learn to look), and "what is this letter?".
 */
import { weave } from './lesson'
import { shuffled } from '../text/shuffle'
import { moduleOf } from './worlds'

export const MODULE = moduleOf('letters')
export const keyOfLetter = (letter) => letter.id

const TATWEEL = 'ـ'

/** How a letter is written at the start, middle and end of a word: one that never joins the next looks the same at the start. */
export const formsOf = ({ letter, joins }) => (joins
  ? [`${letter}${TATWEEL}`, `${TATWEEL}${letter}${TATWEEL}`, `${TATWEEL}${letter}`]
  : [letter, `${TATWEEL}${letter}`, `${TATWEEL}${letter}`])

const joinLine = (letter) => {
  const [start, middle, end] = formsOf(letter)
  return letter.joins
    ? `In a word: ${start} at the start, ${middle} in the middle, ${end} at the end.`
    : `It never joins the letter after it: ${start} at the start, ${end} after a letter.`
}

/** Two other letters for the options: its own shape's first, then any. */
function othersOf(letter, all, random) {
  const kin = shuffled(all.filter((one) => one.family === letter.family && one.id !== letter.id), random)
  const rest = shuffled(all.filter((one) => one.family !== letter.family), random)
  return [...kin, ...rest].slice(0, 2)
}

const tagOf = (isNew) => (isNew ? 'New letter' : 'Review')

/** `picked` from lessonItems; `all` every letter. A new letter is asked both ways; a review one way, by chance. */
export function lettersCards(picked, all, random = Math.random) {
  const record = (letter, direction) => ({ module: MODULE, item: keyOfLetter(letter), context: { world: 'letters', direction } })
  const toLetter = (letter, isNew) => {
    const others = othersOf(letter, all, random)
    return {
      kind: 'choose',
      id: `which:${letter.id}`,
      tag: tagOf(isNew),
      ask: `Which one is ${letter.name}?`,
      arabic: true,
      glyph: true,
      options: shuffled([letter, ...others], random).map((one) => ({ id: one.id, text: one.letter })),
      answer: letter.id,
      why: `${letter.letter} is ${letter.name}: ${letter.sound}.`,
      wrong: Object.fromEntries(others.map((one) => [one.id, `That is ${one.name}. ${letter.letter} is ${letter.name}.`])),
      record: record(letter, 'to-letter'),
    }
  }
  const toName = (letter, isNew) => {
    const others = othersOf(letter, all, random)
    return {
      kind: 'choose',
      id: `name:${letter.id}`,
      tag: tagOf(isNew),
      ask: 'What is this letter?',
      ar: letter.letter,
      glyph: true,
      options: shuffled([letter, ...others], random).map((one) => ({ id: one.id, text: one.name })),
      answer: letter.id,
      why: `${letter.letter} is ${letter.name}: ${letter.sound}.`,
      record: record(letter, 'to-name'),
    }
  }
  return weave(picked, {
    teach: (letter) => ({ kind: 'teach', id: `teach:${letter.id}`, tag: 'New letter', glyph: true, ar: letter.letter, en: `${letter.name} · ${letter.sound}`, note: joinLine(letter) }),
    asks: (letter, isNew) => (isNew ? [toLetter(letter, true), toName(letter, true)] : [random() < 0.5 ? toLetter(letter, false) : toName(letter, false)]),
  })
}
