/** Up to a few places left open in other tabs, each one tap back in. */
import { TABS } from '../../lib/tabs'

const labelFor = (id) => TABS.find((tab) => tab.id === id)?.label ?? id

export default function ContinueRow({ places, title, onGo }) {
  if (places.length === 0) return null
  return (
    <section className="space-y-2" aria-label={title}>
      <h3 className="type-small font-bold text-[var(--text-dim)]">{title}</h3>
      <ul className="flex flex-wrap gap-2">
        {places.map((step) => (
          <li key={step.tab}>
            <button type="button" onClick={() => onGo(step.tab, step.value)} dir="auto"
              className="tap press type-small px-3 rounded-full border border-[var(--border)] text-[var(--text)]
                hover:bg-[var(--surface)] max-w-full truncate">
              <span className="font-bold">{labelFor(step.tab)}</span>
              {' '}<span className="text-[var(--text-dim)]">{step.value}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
