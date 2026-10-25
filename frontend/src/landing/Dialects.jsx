/**
 * A taste of Colloquial: the dialects it teaches, each drawn the same way the
 * course picker itself draws a dialect card (CountryMap, CountryIcons), so a
 * visitor sees the shape and the flags before ever opening the app. The data
 * is a small display-only trim of the real catalogue (dialectsPreview.json),
 * since the landing page has no query client to fetch the live one.
 */
import { colorFor } from '../theme'
import { CountryIcons, CountryMap } from '../components/colloquial/CountryMap'
import Reveal from './Reveal'
import dialectFile from '../lib/colloquial/dialectsPreview.json'

const { dialects } = dialectFile

export default function Dialects() {
  const hue = colorFor('tab', 'colloq')
  return (
    <section className="landing-dialects" aria-labelledby="landing-dialects-title">
      <div className="wrap">
        <Reveal as="h2" id="landing-dialects-title">Spoken Arabic, dialect by dialect.</Reveal>
        <Reveal as="p" className="type-ui text-[var(--muted)] mt-2 max-w-[42ch]">
          Colloquial teaches each one in its own country and its own voice.
        </Reveal>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
          {dialects.map((d, i) => (
            <Reveal key={d.key} style={{ '--i': i }}
              className="landing-dialects-card flex flex-col items-center gap-2 px-3 py-4 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]">
              <CountryMap codes={d.countries} cities={d.cities} hue={hue} className="w-full max-w-24" />
              <span className="type-ui font-semibold text-[var(--text)]">{d.label}</span>
              <CountryIcons codes={d.countries} most={2} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
