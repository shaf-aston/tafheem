/**
 * The passages a reader kept, each with its citation and the opening of its
 * text, under the results: the tab re-asks the last question on arrival, so a
 * list shown only on an empty page would never be seen.
 *
 * What is kept is the passage as the search returned it, so a saved quotation
 * reads the same after the index is rebuilt.
 */
import { useSavedState } from '../../lib/store/stored'
import SmallButton from '../ui/buttons/SmallButton'
import OpeningRow from './OpeningRow'
import { SAVED_ID, SAVED_KEY, citeOf } from './cite'

export default function SavedPassages({ onOpen }) {
  const [saved, setSaved] = useSavedState(SAVED_KEY, [])
  if (!saved.length) return null

  return (
    <section id={SAVED_ID} className="space-y-2 scroll-mt-24" aria-label="Saved passages">
      <h3 className="eyebrow">Saved passages · {saved.length}</h3>
      <ul className="space-y-2">
        {saved.map((hit) => (
          <li key={hit.id} className="flex items-center gap-3">
            <OpeningRow hit={hit} onOpen={onOpen} />
            <SmallButton aria-label={`Remove ${citeOf(hit)}`}
              onClick={() => setSaved((all) => all.filter((h) => h.id !== hit.id))}>
              Remove
            </SmallButton>
          </li>
        ))}
      </ul>
    </section>
  )
}
