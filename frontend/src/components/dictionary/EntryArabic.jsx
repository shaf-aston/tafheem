/**
 * The Arabic of a Maqayees entry, laid out the way the book lays it out.
 * Shared by the card's passages and the line-by-line views.
 */
import { entryLines } from '../../lib/entryLines'

import ArabicText from '../ui/ArabicText'

/**
 * One line of the entry, laid out the way the book lays it out.
 *
 * A verse is one thought in two halves with a gap down the middle of the page,
 * and printing it as a sentence loses the shape that makes it readable as
 * poetry. Everything else is prose against the right edge. Full width at the
 * reading size: a capped measure left half the card empty and doubled the
 * scrolling.
 */
export const Line = ({ line, size = 'base', style }) => (line.halves ? (
  <div className="flex flex-wrap justify-center gap-x-10 gap-y-1" dir="rtl" style={style}>
    {line.halves.map((half, i) => <ArabicText key={i} size={size}>{half}</ArabicText>)}
  </div>
) : (
  <ArabicText as="p" size={size} style={style}>
    {line.text}
  </ArabicText>
))

/** Every line of a passage, laid out. Every Arabic passage on the card shares it. */
export const Lines = ({ text, size, style }) =>
  entryLines(text).map((line, i) => <Line key={i} line={line} size={size} style={style} />)
