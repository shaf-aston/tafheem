/**
 * One quiet line saying what happened to the request: a word swapped, a
 * search narrowed, a link that named nothing. Read out when it changes.
 * Not for an empty result (EmptyState) or a failure (ErrorAlert).
 */
import { isArabic } from '../../lib/arabicText'

import ArabicText from './ArabicText'

export default function StatusNote({ children }) {
  return <p role="status" className="type-small text-[var(--text-dim)]">{children}</p>
}

/** A word quoted in the line, set in its own script and a shade brighter. */
export function NoteWord({ text }) {
  return isArabic(text)
    ? <ArabicText as="span" size="tiny" className="text-[var(--text)]">{text}</ArabicText>
    : <span className="text-[var(--text)]">{text}</span>
}

/** The typed words a search did not know and the known words it searched instead. */
export function CorrectedNote({ corrected }) {
  if (!corrected?.length) return null
  return (
    <StatusNote>
      {corrected.map(({ typed, used }, i) => (
        <span key={typed}>
          {i > 0 && ', '}
          searched <NoteWord text={used} /> for <NoteWord text={typed} />
        </span>
      ))}
    </StatusNote>
  )
}
