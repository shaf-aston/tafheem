/**
 * How to read the letters under the Arabic: "3" is the sound ع, "kh" is خ. Each dialect's own key
 * (a unit carries it as `transliteration_key`), folded away so it costs a learner nothing until
 * wanted, and always one tap from any topic. Nothing is drawn for a unit without one, nor while the
 * learner has the spelling switched off (parts/Spelling), when there is nothing here to read.
 */
import { useSetting } from '../../../lib/store/settings'

export default function SpellingKey({ keys }) {
  const on = useSetting('colloq-spelling')
  const entries = Object.entries(keys ?? {})
  if (!on || !entries.length) return null
  return (
    <details className="group rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-2">
      <summary className="tap cursor-pointer type-small text-[var(--text-dim)] hover:text-[var(--text)] list-none flex items-center gap-2">
        <span aria-hidden="true" className="transition-transform group-open:rotate-90">›</span>
        How to read the spelling
      </summary>
      <dl className="mt-2 mb-1 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 type-small">
        {entries.map(([letters, sound]) => (
          <div key={letters} className="contents">
            <dt className="font-semibold text-[var(--text)] tabular-nums">{letters}</dt>
            <dd dir="auto" className="text-[var(--text-dim)] justify-self-start">{sound}</dd>
          </div>
        ))}
      </dl>
    </details>
  )
}
