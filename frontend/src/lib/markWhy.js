/**
 * What a recited word's mark means in a sentence, and which part of the word
 * the ear doubted. Pure, so the card that shows them has nothing to decide.
 */
import { bareForm, sameSpokenWord } from './arabicText'
import { CHECK, MISSED, SAID, WAITING, WRONG } from './follow'

/** One plain sentence for why a word is marked as it is. */
export const whyOf = (mark) => {
  if (mark.state === WAITING) return 'Not reached yet.'
  if (mark.state === SAID) return 'Said right.'
  if (mark.state === MISSED) return 'Not heard.'
  if (mark.state === CHECK) return 'The model could not confirm this word. It may be your slip or a mishearing.'
  if (mark.state === WRONG) {
    return mark.said && sameSpokenWord(mark.said, mark.word)
      ? 'The letters matched but the sound did not, likely a vowel or letter slip at the underlined part.'
      : 'A different word was heard.'
  }
  return ''
}

// Marks stripped and the alif forms folded, so a piece the ear spelt plainly
// is found inside the page's printed word.
const plain = (text) => bareForm(text).replace(/ٱ/g, 'ا')
const isMark = (char) => bareForm(char) === ''

/**
 * The word split around its weak piece, [before, piece, after], matched by
 * letters alone and returned with the page's own marks. Null when the piece
 * is missing, has no letters, or is not in the word.
 */
export const weakParts = (word, weak) => {
  const piece = plain(weak ?? '').replace(/\s/g, '')
  if (!piece) return null
  const letters = [...word]
  const bare = letters.map((char) => (isMark(char) ? '' : plain(char)))
  const folded = bare.join('')
  const start = folded.indexOf(piece)
  if (start < 0) return null
  // Walk the printed characters, counting letters, so the cut lands on the
  // page's own spelling; marks after the last letter of the piece stay with it.
  let seen = 0
  let from = -1
  let to = letters.length
  letters.forEach((char, i) => {
    if (!bare[i]) return
    if (seen === start && from < 0) from = i
    seen += bare[i].length
    if (seen >= start + piece.length && to === letters.length) to = i + 1
  })
  while (to < letters.length && isMark(letters[to])) to += 1
  return [letters.slice(0, from).join(''), letters.slice(from, to).join(''), letters.slice(to).join('')]
}
