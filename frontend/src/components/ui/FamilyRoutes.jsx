/**
 * How many narrators carry a hadith number at each place of its chains, as a small layered picture: a row per place
 * counted from the Companion, a dot per narrator, the thinnest place in the accent. Under it the term that place
 * gives, always as our count within the books the app holds and with Ibn Hajar's own words behind it, never as a
 * verdict. Nothing is drawn where the build could not line the chains up (routes is null).
 */
import ArabicText from './ArabicText'
import Disclosure from './Disclosure'

const placeLabel = (i) => (i === 0 ? 'Companion' : `Place ${i + 1}`)
const narrators = (n) => `${n} ${n === 1 ? 'narrator' : 'narrators'}`

function Cite({ say, cite }) {
  return (
    <div className="space-y-0.5">
      {say && <p className="type-tiny m-0 text-[var(--text-faint)]">{say}</p>}
      <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text)]">{cite.quote}</ArabicText>
      <p className="type-tiny m-0 text-[var(--text-faint)]">{[cite.source, cite.page].filter(Boolean).join(', ')}</p>
    </div>
  )
}

export default function FamilyRoutes({ routes, tellings, accent }) {
  if (!routes) return null
  const { layers, thinnest } = routes
  return (
    <section aria-label="Narrators at each place of the chains" data-routes className="space-y-2">
      <p className="type-small m-0 text-[var(--text-dim)]">
        Our count, {routes.scope}: {narrators(thinnest)} at the thinnest place of {tellings} tellings.
        {' '}<ArabicText size="sm" className="text-[var(--text)]">{routes.ar}</ArabicText>
        <span className="text-[var(--text-faint)]"> is Ibn Hajar&apos;s word for {routes.say}.</span>
      </p>
      <ul className="list-none m-0 p-0 space-y-1">
        {layers.map((n, i) => (
          <li key={placeLabel(i)} className="flex items-center gap-2" aria-label={`${placeLabel(i)}: ${narrators(n)}`}>
            <span aria-hidden="true" className="type-tiny w-16 shrink-0 text-[var(--text-faint)]">{placeLabel(i)}</span>
            <span aria-hidden="true" className="flex flex-wrap items-center gap-1 min-w-0">
              {Array.from({ length: n }, (_, d) => (
                <span
                  key={d}
                  style={n === thinnest ? { background: accent, borderColor: accent } : undefined}
                  className="w-2 h-2 rounded-full border border-[var(--text-faint)]"
                />
              ))}
            </span>
            <span aria-hidden="true" className="type-tiny tabular-nums text-[var(--text-faint)]">{n}</span>
          </li>
        ))}
      </ul>
      <p className="type-tiny m-0 text-[var(--text-faint)]">{routes.place_note}</p>
      <Disclosure label="Ibn Hajar's words, Nuzhat al-Nazar">
        <div className="space-y-3">
          <Cite cite={routes.definition} />
          <Cite say={routes.layer_rule.say} cite={routes.layer_rule} />
        </div>
      </Disclosure>
    </section>
  )
}
