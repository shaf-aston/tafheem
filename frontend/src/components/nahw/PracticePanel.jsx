import { useState } from 'react'

import { errorMessage } from '../../lib/api/apiError'

import Disclosure from '../ui/overlays/Disclosure'
import SourceBadge from '../ui/feedback/SourceBadge'

// One row of the extras under an analysis. Opening it is the ask: the questions
// are made the first time it opens, so there is no separate Generate step.
export default function PracticePanel({ practice, sentence, accent }) {
  const make = () => practice.mutate(sentence)
  return (
    <Disclosure
      ruled
      label="Practice questions"
      hint="Check you followed this sentence"
      onToggle={(open) => { if (open && !practice.data && !practice.isPending) make() }}
    >
      {practice.isPending && <p className="type-ui text-[var(--text-faint)]">Making questions…</p>}
      {practice.isError && (
        <p className="type-ui" style={{ color: 'var(--danger)' }}>
          {errorMessage(practice.error, 'Could not make questions.')}{' '}
          <button type="button" onClick={make} className="underline underline-offset-2">Try again</button>
        </p>
      )}
      {practice.data && !practice.isPending && (
        <PracticeQuestions data={practice.data} accent={accent} onMore={make} />
      )}
    </Disclosure>
  )
}

function PracticeQuestions({ data, accent, onMore }) {
  const [revealed, setRevealed] = useState({})

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onMore}
          style={{ color: accent }}
          className="type-label underline underline-offset-2 hover:opacity-80 transition-opacity"
        >
          New questions
        </button>
        <SourceBadge source={data.source} />
      </div>
      {data.questions.map((q, i) => (
        <div
          key={i}
          style={{ '--i': i }}
          className="rise-in p-4 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)] space-y-2"
        >
          <p className="type-ui font-medium text-[var(--text)]">{i + 1}. {q.question}</p>
          {q.hint && !revealed[i] && (
            <p className="type-label text-[var(--text-faint)] italic">Hint: {q.hint}</p>
          )}
          {revealed[i] ? (
            <div
              className="fade-in p-3 rounded-[var(--radius-sm)] type-ui"
              style={{
                color: 'var(--success)',
                background: 'var(--success-wash)',
              }}
            >
              {q.answer}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setRevealed((r) => ({ ...r, [i]: true }))}
              style={{ '--c': accent, color: accent }}
              className="type-label underline underline-offset-2 hover:opacity-80 transition-opacity"
            >
              Show answer
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
