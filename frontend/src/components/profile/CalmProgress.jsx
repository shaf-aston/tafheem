/**
 * Progress told calmly, top first, in the profile and Home's progress column alike: this week (a dot a day and a
 * few plain counts, with no streak to lose), then how much of the Qur'an the words known reach. The level, the
 * streak and the rankings follow below them in each view, quieter. Figures from lib/learner/useProgressFacts.
 */
import { useId } from 'react'

import { weekOf } from '../../lib/learner/week'
import { colorFor } from '../../theme'
import { Skeleton } from '../ui/feedback/Skeleton'

// Said of a day, for a screen reader and a pointer's tooltip; the dot alone says it to the eye.
const SAYS = { studied: 'studied', rest: 'no answers', unknown: 'not in the record', ahead: 'still to come' }

/** The week's dots, words met and known, answers given, and one line that asks nothing. */
export function ThisWeek({ overview, stats, learnt, account }) {
  const id = useId()
  return (
    <section aria-labelledby={id} className="space-y-4" style={{ '--week-tone': colorFor('tab', 'grow') }}>
      <h3 id={id} className="eyebrow">This week</h3>
      {overview.data ? <Dots overview={overview.data} /> : !overview.isError && <Skeleton className="h-10 w-full" />}
      <dl className="grid grid-cols-3 gap-2">
        <Count name="Words met" value={stats.data?.length} />
        <Count name="Now known" value={stats.data && learnt.length} />
        <Count name="Answers" value={account.data?.answers} />
      </dl>
      <p className="type-small text-[var(--text-dim)]">Come back when you can. Your words wait.</p>
    </section>
  )
}

function Dots({ overview }) {
  return (
    <ol className="week-dots">
      {weekOf(overview).map(({ date, state, today }) => {
        const says = `${date.toLocaleDateString(undefined, { weekday: 'long' })}: ${SAYS[state]}`
        return (
          <li key={date.getTime()} className={`week-day week-${state}`} title={says}
            aria-current={today ? 'date' : undefined}>
            <span className="week-dot" aria-hidden="true" />
            <span className="type-tiny" aria-hidden="true">{date.toLocaleDateString(undefined, { weekday: 'short' })}</span>
            <span className="sr-only">{says}</span>
          </li>
        )
      })}
    </ol>
  )
}

function Count({ name, value }) {
  return (
    <div className="min-w-0">
      <dt className="type-tiny text-[var(--text-faint)]">{name}</dt>
      <dd className="type-figure font-bold tabular-nums text-[var(--text)]">
        {value ?? <Skeleton className="h-6 w-10" />}
      </dd>
    </div>
  )
}

/** How much of the Qur'an's running text the words known cover: the one measure of understanding the record has. */
export function Understanding({ share, covered }) {
  const id = useId()
  return (
    <section aria-labelledby={id} className="space-y-2" style={{ '--xp-tone': colorFor('tab', 'grow') }}>
      <h3 id={id} className="eyebrow">How much you understand</h3>
      {covered === null ? <Skeleton className="h-10 w-full" /> : (
        <>
          <p className="text-[var(--text-dim)]">
            <span className="type-figure font-bold tabular-nums text-[var(--text)]">{covered}</span> of the Qur’an’s words
          </p>
          <div className="xp-bar" role="progressbar" aria-label="Of the Qur’an’s words" aria-valuemin={0}
            aria-valuemax={100} aria-valuenow={Math.round(100 * (share ?? 0))}>
            <span style={{ '--xp-share': share ?? 0 }} />
          </div>
        </>
      )}
      <p className="type-small text-[var(--text-faint)]">A word you know counts every time it comes in the Qur’an.</p>
    </section>
  )
}

/** One quiet row of the detail further down: a name and its figure, no box. */
export function Fact({ name, value }) {
  return (
    <div className="calm-row">
      <dt className="type-small text-[var(--text-faint)]">{name}</dt>
      <dd className="type-small font-bold tabular-nums text-[var(--text)]">
        {value || value === 0 ? value : <Skeleton className="h-4 w-12" />}
      </dd>
    </div>
  )
}
