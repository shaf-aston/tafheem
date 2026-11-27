/** Where no passage answers: the closest few, named as just that, each with its opening words and opening in its book. */
import OpeningRow from './OpeningRow'

export default function Closest({ hits, onOpen }) {
  if (!hits.length) return null
  return (
    <section className="space-y-2" aria-label="Closest, but not an answer">
      <h3 className="eyebrow">Closest, but not an answer</h3>
      <ul className="space-y-2">
        {hits.map((hit) => <li key={hit.id}><OpeningRow hit={hit} onOpen={onOpen} /></li>)}
      </ul>
    </section>
  )
}
