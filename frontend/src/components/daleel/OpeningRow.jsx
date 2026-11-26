/** A passage in a list: its citation over its opening words, a press opens it in its book. */
import { mostlyArabic } from '../../lib/text/arabicText'
import ArabicText from '../ui/text/ArabicText'
import { citeOf, openingOf } from './cite'

export default function OpeningRow({ hit, onOpen }) {
  const opening = openingOf(hit)
  return (
    <button type="button" onClick={() => onOpen(hit)} className="press tap w-full flex-1 min-w-0 text-start space-y-1">
      <span className="block type-small text-[var(--text-faint)]">{citeOf(hit)}</span>
      {mostlyArabic(opening)
        ? <ArabicText size="tiny" className="block truncate text-[var(--text-dim)]">{opening}</ArabicText>
        : <span className="block truncate type-small text-[var(--text-dim)]">{opening}</span>}
    </button>
  )
}
