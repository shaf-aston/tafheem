/** Where no passage answers: the closest few, named as just that, each with its opening words and opening in its book. */
import { mostlyArabic } from '../../lib/text/arabicText'
import ArabicText from '../ui/text/ArabicText'
import { citeOf, openingOf } from './cite'

export default function Closest({ hits, onOpen }) {
  if (!hits.length) return null
  return (
    <section className="space-y-2" aria-label="Closest, but not an answer">
      <h3 className="eyebrow">Closest, but not an answer</h3>
      <ul className="space-y-2">
        {hits.map((hit) => (
          <li key={hit.id}>
            <button type="button" onClick={() => onOpen(hit)} className="press tap w-full min-w-0 text-start space-y-1">
              <span className="block type-small text-[var(--text-faint)]">{citeOf(hit)}</span>
              {mostlyArabic(openingOf(hit))
                ? <ArabicText size="tiny" className="block truncate text-[var(--text-dim)]">{openingOf(hit)}</ArabicText>
                : <span className="block truncate type-small text-[var(--text-dim)]">{openingOf(hit)}</span>}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
