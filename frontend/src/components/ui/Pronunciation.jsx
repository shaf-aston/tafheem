/**
 * How a word sounds, printed beside the word itself.
 *
 * One component for two reasons. It is the only place the academic spelling is
 * converted, so the scheme cannot be applied in the dictionary and forgotten in
 * the word grid. And it is the only place this line is styled, which the two
 * callers had already started disagreeing about, one on a raw text-sm and the
 * other on the type-small token.
 *
 * Not italic. Italics lean and thin exactly the marks this text is made of, and
 * a leaning apostrophe beside a doubled vowel is where "hard to read" comes
 * from. text-dim rather than text-faint for the same reason: quieter than the
 * Arabic it sits next to, but not so pale that a reader has to hunt for it.
 *
 * Always dir="ltr". It sits inside a right-to-left block, and left to itself an
 * English word ending in an apostrophe gets that apostrophe thrown to the front.
 *
 * Size is a prop rather than a class the caller writes, the same rule
 * ArabicText follows, so this line can only ever be one of the app's own sizes.
 * Two are enough: a full entry gives it the reading size, because there it is
 * something a reader sounds out; a grid card, which packs many words into a
 * line, keeps the label size.
 */
import { plainPronunciation } from '../../lib/pronounce'

const SIZES = { small: 'type-small', body: 'type-body' }

export default function Pronunciation({ children, size = 'small', className = '' }) {
  const said = plainPronunciation(children)
  if (!said) return null

  return (
    <span dir="ltr" className={`${SIZES[size]} text-[var(--text-dim)] ${className}`.trim()}>
      {said}
    </span>
  )
}
