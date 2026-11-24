/** Where no passage answers: the closest few, named as just that, each opening in its book. */
import { citeOf } from './cite'

export default function Closest({ hits, onOpen }) {
  if (!hits.length) return null
  return (
    <section className="space-y-2" aria-label="Closest, but not an answer">
      <h3 className="eyebrow">Closest, but not an answer</h3>
      <ul className="space-y-1">
        {hits.map((hit) => (
          <li key={hit.id}>
            <button type="button" onClick={() => onOpen(hit)}
              className="press tap type-small underline underline-offset-4 text-[var(--text-dim)]">
              {citeOf(hit)}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
