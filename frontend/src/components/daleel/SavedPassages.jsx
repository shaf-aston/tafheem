/**
 * The passages a reader kept, each with its citation and the opening of its
 * text, under the results: the tab re-asks the last question on arrival, so a
 * list shown only on an empty page would never be seen.
 *
 * What is kept is the passage as the search returned it, so a saved quotation
 * reads the same after the index is rebuilt.
 */
import { mostlyArabic } from '../../lib/text/arabicText'
import { useSavedState } from '../../lib/store/stored'
import ArabicText from '../ui/text/ArabicText'
import SmallButton from '../ui/buttons/SmallButton'
import { SAVED_ID, SAVED_KEY, citeOf, openingOf } from './cite'


export default function SavedPassages({ onOpen }) {
  const [saved, setSaved] = useSavedState(SAVED_KEY, [])
  if (!saved.length) return null

  return (
    <section id={SAVED_ID} className="space-y-2 scroll-mt-24" aria-label="Saved passages">
      <h3 className="eyebrow">Saved passages · {saved.length}</h3>
      <ul className="space-y-2">
        {saved.map((hit) => {
          const text = hit.arabic || hit.english
          return (
            <li key={hit.id} className="flex items-center gap-3">
              <button type="button" onClick={() => onOpen(hit)} className="press tap flex-1 min-w-0 text-start space-y-1">
                <span className="block type-small text-[var(--text-faint)]">{citeOf(hit)}</span>
                {mostlyArabic(text)
                  ? <ArabicText size="tiny" className="block truncate text-[var(--text-dim)]">{openingOf(hit)}</ArabicText>
                  : <span className="block truncate type-small text-[var(--text-dim)]">{openingOf(hit)}</span>}
              </button>
              <SmallButton aria-label={`Remove ${citeOf(hit)}`}
                onClick={() => setSaved((all) => all.filter((h) => h.id !== hit.id))}>
                Remove
              </SmallButton>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
