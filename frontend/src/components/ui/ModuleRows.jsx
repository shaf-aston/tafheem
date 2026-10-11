/** One row per module someone answered in: words learnt, answers given, the last day. */
import { TABS } from '../../lib/tabs'

import { Skeleton } from './Skeleton'

// A module id is a tab's id, optionally with a language ("quiz:ur"); anything else shows as it is.
const nameOf = (module) => {
  const [base, ...rest] = module.split(':')
  const tab = TABS.find((one) => one.id === base)
  return tab ? [tab.label, ...rest].join(' · ') : module
}

export default function ModuleRows({ overview }) {
  if (overview.isPending) return <Skeleton className="h-16 w-full" />
  if (overview.isError) return <p className="type-small text-[var(--danger)]">Could not load the modules.</p>
  const { modules } = overview.data
  if (modules.length === 0) return <p className="type-small text-[var(--text-faint)]">No answers yet.</p>
  return (
    <section className="space-y-2">
      <h3 className="type-small font-bold text-[var(--text-dim)]">Modules</h3>
      <ul className="space-y-1">
        {modules.map((row) => (
          <li key={row.module}
            className="flex flex-wrap items-baseline gap-x-3 px-3 py-1.5 rounded-[var(--radius-sm)] type-small text-[var(--text-dim)]">
            <span dir="auto" className="flex-1 min-w-[6rem] truncate font-bold text-[var(--text)]">{nameOf(row.module)}</span>
            <span className="tabular-nums">{row.learnt} learnt</span>
            <span className="tabular-nums">{row.attempts} {row.attempts === 1 ? 'answer' : 'answers'}</span>
            <span className="tabular-nums text-[var(--text-faint)]">{new Date(row.lastAt).toLocaleDateString()}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
