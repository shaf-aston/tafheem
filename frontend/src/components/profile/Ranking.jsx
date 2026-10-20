/**
 * A ranking by words learnt, the global one or one circle's: your row stands
 * out, and is added below when you are not among the rows shown.
 */
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'

export default function Ranking({ board, name, title }) {
  if (board.isPending) return <Skeleton className="h-24 w-full" />
  if (board.isError) return <ErrorAlert inline title="Could not load the ranking." onRetry={() => board.refetch()} />
  const { rows, you } = board.data
  const shown = you && !rows.some((row) => row.name === name) ? [...rows, you] : rows
  return (
    <section className="space-y-2">
      <h3 className="type-small font-bold text-[var(--text-dim)]">{title}</h3>
      <ol className="space-y-1">
        {shown.map((row) => {
          const mine = row.name === name
          return (
            <li
              key={row.name}
              className={`flex items-center gap-3 px-3 py-1.5 rounded-[var(--radius-sm)] type-small ${
                mine ? 'bg-[var(--surface-hi)] font-bold text-[var(--palette-gold)]' : 'text-[var(--text-dim)]'}`}
            >
              <span className="w-6 tabular-nums">{row.rank}</span>
              <span dir="auto" className="flex-1 truncate">{mine ? `${row.name} (you)` : row.name}</span>
              <span className="tabular-nums">{row.learnt} learnt</span>
              <span className="tabular-nums text-[var(--text-faint)]">{row.answers} {row.answers === 1 ? 'answer' : 'answers'}</span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
