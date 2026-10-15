import { useState } from 'react'

import { errorMessage } from '../../lib/apiError'

import SourceBadge from '../ui/SourceBadge'

export default function PracticePanel({ practice, sentence, accent }) {
  return (
    <div className="border-t border-[var(--border)] pt-4">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div>
          <div className="text-sm font-medium text-[var(--text)]">Practice questions</div>
          <div className="text-xs text-[var(--text-faint)]">Check you followed this sentence</div>
        </div>
        <button
          type="button"
          onClick={() => practice.mutate(sentence)}
          disabled={practice.isPending}
          style={{ '--c': accent, color: accent }}
          className="px-4 py-1.5 text-sm rounded-[var(--radius-md)] border border-[var(--border)]
            hover:border-[var(--c)] disabled:opacity-50 transition-colors"
        >
          {practice.isPending ? 'Generating…' : 'Generate'}
        </button>
      </div>

      {practice.isError && (
        <p className="text-sm" style={{ color: 'var(--danger)' }}>
          {errorMessage(practice.error, 'Could not generate questions.')}
        </p>
      )}
      {practice.data && !practice.isPending && (
        <PracticeQuestions data={practice.data} accent={accent} />
      )}
    </div>
  )
}

function PracticeQuestions({ data, accent }) {
  const [revealed, setRevealed] = useState({})

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <SourceBadge source={data.source} />
      </div>
      {data.questions.map((q, i) => (
        <div
          key={i}
          style={{ '--i': i }}
          className="rise-in p-4 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)] space-y-2"
        >
          <p className="text-sm font-medium text-[var(--text)]">{i + 1}. {q.question}</p>
          {q.hint && !revealed[i] && (
            <p className="text-xs text-[var(--text-faint)] italic">Hint: {q.hint}</p>
          )}
          {revealed[i] ? (
            <div
              className="fade-in p-3 rounded-[var(--radius-sm)] text-sm"
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
              className="text-xs underline underline-offset-2 hover:opacity-80 transition-opacity"
            >
              Show answer
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
