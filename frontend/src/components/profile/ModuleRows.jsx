/** One row per module someone answered in: words learnt, answers given, the last day. */
import { labelOf } from '../../lib/nav/moduleTab'

import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'

export default function ModuleRows({ overview }) {
  if (overview.isPending) return <Skeleton className="h-16 w-full" />
  if (overview.isError) return <ErrorAlert inline title="Could not load the modules." onRetry={() => overview.refetch()} />
  const { modules } = overview.data
  if (modules.length === 0) return <p className="type-small text-[var(--text-faint)]">No answers yet.</p>
  return (
    <section className="space-y-2">
      <h3 className="type-small font-bold text-[var(--text-dim)]">Modules</h3>
      <ul className="space-y-1">
        {modules.map((row) => (
          <li key={row.module}
            className="flex flex-wrap items-baseline gap-x-3 px-3 py-1.5 rounded-[var(--radius-sm)] type-small text-[var(--text-dim)]">
            <span dir="auto" className="flex-1 min-w-[6rem] truncate font-bold text-[var(--text)]">{labelOf(row.module)}</span>
            <span className="tabular-nums">{row.learnt} learnt</span>
            <span className="tabular-nums">{row.attempts} {row.attempts === 1 ? 'answer' : 'answers'}</span>
            <span className="tabular-nums text-[var(--text-faint)]">{new Date(row.lastAt).toLocaleDateString()}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
