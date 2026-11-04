/**
 * How many different narrators stand at each place of the chains one book gives under one number: a row per place
 * counted from the Companion, a dot per narrator. A place one narrator carries in every narration is in the accent
 * and says so. The words all come from the server (usul.json family.places); nothing is drawn where the build left
 * the family without a picture (places is null).
 */
export default function FamilyPlaces({ places, accent }) {
  if (!places) return null
  return (
    <section aria-label={places.heading} data-places className="space-y-2">
      <p className="type-small m-0 text-[var(--text-dim)]">{places.heading}</p>
      <ul className="list-none m-0 p-0 space-y-1">
        {places.places.map((p) => (
          <li key={p.label} className="flex flex-wrap items-center gap-x-2 gap-y-0.5" aria-label={`${p.label}: ${p.count}${p.alone ? `, ${p.alone}` : ''}`}>
            <span aria-hidden="true" className="type-tiny w-16 shrink-0 text-[var(--text-faint)]">{p.label}</span>
            <span aria-hidden="true" className="flex flex-wrap items-center gap-1 min-w-0">
              {Array.from({ length: p.count }, (_, d) => (
                <span
                  key={d}
                  style={p.alone ? { background: accent, borderColor: accent } : undefined}
                  className="w-2 h-2 rounded-full border border-[var(--text-faint)]"
                />
              ))}
            </span>
            <span aria-hidden="true" className="type-tiny tabular-nums text-[var(--text-faint)]">{p.count}</span>
            {p.alone && <span aria-hidden="true" style={{ color: accent }} className="type-tiny">{p.alone}</span>}
          </li>
        ))}
      </ul>
      <p className="type-tiny m-0 text-[var(--text-faint)]">{places.note}</p>
    </section>
  )
}
