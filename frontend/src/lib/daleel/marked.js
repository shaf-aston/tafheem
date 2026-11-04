/**
 * Words the server marked, carried through text that is reshaped on the way.
 *
 * The server says where the words that made a quotation match are, as
 * [start, end) offsets into the text as stored. The screen then reshapes that
 * text (Lane's entries are mended and re-lined) before drawing it, so the
 * offsets would point at the wrong letters by then. Instead the marks go into
 * the text itself, as two private-use characters no book contains, and ride
 * through whatever string-to-string step comes next. Drawing splits on them.
 *
 * Offsets count code points, as Python's do, not UTF-16 units.
 */
const START = ''
const END = ''
const SPLIT = new RegExp(`(${START}[^${END}]*${END})`)

/** The text with each [start, end) span wrapped in the two marks. */
export function withMarks(text, spans) {
  if (!text || !spans?.length) return text ?? ''
  const letters = Array.from(text)
  // From the end, so the offsets still ahead are not moved by an insertion.
  for (const [start, end] of [...spans].sort((a, b) => b[0] - a[0])) {
    if (start < 0 || end > letters.length || start >= end) continue
    letters.splice(end, 0, END)
    letters.splice(start, 0, START)
  }
  return letters.join('')
}

/** The text cut at the marks, each piece saying whether it was marked. */
export function markedPieces(text) {
  return (text ?? '').split(SPLIT).filter(Boolean).map((piece) => piece.startsWith(START)
    ? { text: piece.slice(1, -1), marked: true }
    : { text: piece.replaceAll(START, '').replaceAll(END, ''), marked: false })
}
