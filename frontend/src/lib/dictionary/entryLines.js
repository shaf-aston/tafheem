/**
 * The lines of a Maqāyīs entry, as the editor set them.
 *
 * The printed entry is not one block of prose. Hārūn breaks a line wherever a
 * line of poetry ends, and those breaks are in the text we ship. Run together
 * they read as a wall, so the card lays each one out on its own.
 *
 * A line of classical poetry is one verse in two halves, printed with a gap
 * down the middle of the page. The book marks that gap with " ... ", which is
 * the only structure inside a line worth reading, so it is the only one this
 * looks for. A line with any other number of gaps is left as prose rather than
 * cut at a guess.
 */
import config from '../../config/dictionary.json'

/** The gap between the two halves of a verse, as the book writes it. */
const VERSE_GAP = ' ... '

/**
 * Split an entry body into its lines.
 * @param {string} body
 * @returns {{text: string, halves: string[] | null}[]} halves is set only on a
 *   verse, two pieces, in the order they are printed.
 */
export function entryLines(body) {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((text) => {
      const halves = text.split(VERSE_GAP)
      return { text, halves: halves.length === 2 ? halves : null }
    })
}

/**
 * Lisan and Taj al-Arus entries as paragraphs to read.
 *
 * Taj al-Arus arrives broken at every printed line, so it read as a column of
 * forty-letter scraps; Lisan arrives as one block with no break at all. Both
 * are the same fix: join the printed lines, cut at each full stop, and gather
 * sentences until a paragraph is long enough to read as one. A blank line is
 * kept: the server puts it where a book returns to the root in a later volume.
 * The length is dictionary.json's entry.paragraph-letters.
 */
const LETTERS = config.entry['paragraph-letters']

// After a full stop or question mark, never inside the "..." between the two
// halves of a verse, and never inside a number (3.5): the mark must have space
// or the end after it. Never after one Arabic letter standing alone either: that
// is a short form (د. for doctor, ص. for page), not the end of a sentence. An
// ayah's number in its brackets (﴿٣﴾) ends one too: a verse copied in carries no
// full stop.
const END = String.raw`(?<!\.)(?<!(?:^|\s)[ء-ي])[.؟!?]|[0-9٠-٩]﴾`
const SENTENCE_END = new RegExp(`(?<=${END})\\s+`, 'u')

/** Whether a paragraph has a full stop anywhere in it: prose, cut into sentences, not a list of lines. */
export const hasSentenceEnd = (part) => new RegExp(`(?:${END})(?=\\s|$)`, 'u').test(part)

/** The sentences of one paragraph: its printed lines joined, then cut after each full stop. */
export const sentencesOf = (part) => part.replace(/\s*\n\s*/g, ' ').trim().split(SENTENCE_END).filter(Boolean)

/** Text cut at its blank lines, each part trimmed, empty parts dropped. */
export const blocksOf = (text) => (text ?? '').split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean)

export function paragraphs(text) {
  return blocksOf(text).flatMap((part) => {
    const said = []
    let run = ''
    for (const sentence of sentencesOf(part)) {
      run = run ? `${run} ${sentence}` : sentence
      if (run.length >= LETTERS) { said.push(run); run = '' }
    }
    if (run) said.push(run)
    return said
  })
}
