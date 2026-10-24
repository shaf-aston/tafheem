/**
 * What a recited word's mark means in a sentence, and which part of the word
 * the ear doubted. Pure, so the card that shows them has nothing to decide.
 */
import { bareForm, sameSpokenWord } from '../arabicText'
import { CHECK, MISSED, SAID, WAITING, WRONG } from '../follow'

/**
 * One plain sentence for why a word is marked as it is. `underlined` is whether
 * the card can point at a part of the word: the sentence only says so when it can.
 */
export const whyOf = (mark, underlined = false) => {
  if (mark.state === WAITING) return 'Not reached yet.'
  if (mark.state === SAID) return 'Said right.'
  if (mark.state === MISSED) return 'Not heard.'
  if (mark.state === CHECK) return 'The model could not confirm this word. It may be your slip or a mishearing.'
  if (mark.state === WRONG) {
    if (!(mark.said && sameSpokenWord(mark.said, mark.word))) return 'A different word was heard.'
    return `The letters matched but the sound did not, likely a vowel or letter slip${underlined ? ' at the underlined part' : ''}.`
  }
  return ''
}

// The alif forms folded, marks kept: the ear's spelling and the page's agree on these.
const spelt = (text) => text.replace(/[أإآٱ]/g, 'ا')
const isMark = (char) => bareForm(char) === ''

/**
 * The word split around its weak piece, [before, piece, after], cut where the
 * ear said the piece starts (`from`, characters into the word) and kept only if
 * the page's own word has the same text there. Marks that trail the piece go
 * with it. Null when there is nothing to cut by, or the piece is only marks,
 * which are drawn on their letter and cannot be underlined alone.
 */
export const weakParts = (word, weak, from) => {
  if (!weak || from == null || !bareForm(weak).trim()) return null
  const letters = [...word]
  if (spelt(letters.slice(from, from + weak.length).join('')) !== spelt(weak)) return null
  let to = from + weak.length
  while (to < letters.length && isMark(letters[to])) to += 1
  return [letters.slice(0, from).join(''), letters.slice(from, to).join(''), letters.slice(to).join('')]
}
