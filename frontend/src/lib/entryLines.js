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

/** The gap between the two halves of a verse, as the book writes it. */
export const VERSE_GAP = ' ... '

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
