// Spaced review: the topic's words that are about to be forgotten, then the ones
// never tried, quizzed the same way as Quiz. What is due comes from the app's one
// review schedule (lib/progress), which every word answer feeds.
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchSummary } from '../../lib/progress'
import { WORDS_MODULE, wordDrills } from '../../lib/wordDrills'
import { reviewOf } from '../../lib/wordReview'
import Practice from './Practice'

const dayOf = (iso) => new Date(iso).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'short' })

// Frozen when it opens, so an answer saved mid-round does not reshuffle the round.
function Round({ words, rows, dialect, offline }) {
  const [plan] = useState(() => reviewOf(words, rows, dialect))
  const [drills] = useState(() => wordDrills(plan.session, 'review', { pool: words, dialect }))
  if (!drills.length) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-6 text-center space-y-1">
        <p className="type-ui font-semibold text-[var(--text)]">All caught up</p>
        <p className="type-small text-[var(--text-dim)]">
          {plan.next ? `The next word comes back ${dayOf(plan.next)}.` : 'Every word here is learnt for now.'}
        </p>
      </div>
    )
  }
  return (
    <div className="space-y-3">
      <p className="type-small text-[var(--text-dim)]">
        {plan.due > 0 && `${plan.due} to remember again`}{plan.due > 0 && plan.fresh > 0 && ' · '}{plan.fresh > 0 && `${plan.fresh} new`}
        {plan.later > 0 && ` · ${plan.later} learnt, resting`}
      </p>
      {offline && <p className="type-small text-[var(--warn)]">Your progress can't be reached, so every word is asked as new and answers may not be saved.</p>}
      <Practice exercises={drills} />
    </div>
  )
}

export default function WordReview({ words, dialect }) {
  const summary = useQuery({
    queryKey: ['progress', WORDS_MODULE],
    queryFn: () => fetchSummary(WORDS_MODULE),
    // The app keeps answers forever by default; what is due changes with every answer.
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
    retry: false,
  })
  // Fetching as well as pending: coming back to Review must not plan from the last visit's answers.
  if (summary.isFetching) return <p className="type-small text-[var(--text-dim)]">Finding the words due…</p>
  return <Round words={words} rows={summary.data ?? []} dialect={dialect} offline={summary.isError} />
}
