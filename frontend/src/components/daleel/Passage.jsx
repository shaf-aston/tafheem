import { mostlyArabic } from '../../lib/text/arabicText'
import { plainEntry } from '../../lib/dictionary/laneEntry'
import { markedPieces, withMarks } from '../../lib/daleel/marked'

import ArabicText from '../ui/text/ArabicText'
import Mark from '../ui/display/Mark'

/**
 * One side of a passage, cut to a few lines when it runs long.
 *
 * Ibn Kathir's entries are whole pages, and set beside an ayah of six words
 * they turned the results into one card and a wall. The cut is not a
 * shortening: the whole passage is a press away, and no card is allowed to
 * decide the height of the page on its own.
 *
 * Both sides fold, not only the English. Every Arabic text Daleel held was
 * short, so the wall could only ever come from a translation; the unabridged
 * Arabic commentaries average a printed page each and put the same wall in the
 * language the reader asked in.
 *
 * ui/ShowRest measures the overflow rather than counting characters, so a
 * passage that happens to fit grows no button. The character threshold this
 * used to keep called a 330-character line long on a phone and on a desktop
 * alike, where it is four lines and one.
 */
export default function Passage({ text, marks, accent, tidy = false, arabic = false, size = 'lg' }) {
  // A dictionary entry arrives with the marks its own dump wrote into it.
  // Every other book passes through untouched, none of them carrying those
  // marks in the first place. The server's marks for the matched words go in
  // first, so they ride through that reshaping and still land on their words.
  const pieces = markedPieces(plainEntry(withMarks(text, marks), { tidy }))
  const said = pieces.map((piece, n) => piece.marked
    ? <Mark key={n} accent={accent}>{piece.text}</Mark>
    : piece.text)

  return arabic && mostlyArabic(pieces.map((piece) => piece.text).join('')) ? (
    <ArabicText size={size} className="block leading-loose whitespace-pre-line">{said}</ArabicText>
  ) : (
    <p className="type-body text-[var(--text-dim)] leading-relaxed whitespace-pre-line max-w-prose">
      {said}
    </p>
  )
}
