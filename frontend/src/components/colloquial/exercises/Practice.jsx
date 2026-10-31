// Practice: one exercise at a time under a row of answer squares.
import { useEffect, useRef, useState } from 'react'

import { scrollToEl } from '../../../lib/motion/scrollToEl'
import AnswerSquare from '../../ui/AnswerSquare'
import SmallButton from '../../ui/SmallButton'
import ExerciseHost from './ExerciseHost'

const ACCENT = 'var(--primary)'

export default function Practice({ exercises }) {
  const [at, setAt] = useState(0)
  const [results, setResults] = useState({})
  const current = exercises[at]
  const answered = current.id in results
  const right = Object.values(results).filter((r) => r.correct).length
  const finished = Object.keys(results).length === exercises.length
  // Next takes focus once an answer is in, so Enter moves on as on the Quiz board;
  // without scrolling, so the answer stays where the learner is looking.
  const nextButton = useRef(null)
  useEffect(() => { if (answered) nextButton.current?.focus({ preventScroll: true }) }, [answered, at])
  // Next unmounts itself, so focus would fall to the page: it goes to the new exercise's first control.
  const body = useRef(null)
  const moved = useRef(false)
  useEffect(() => {
    if (!moved.current) return
    moved.current = false
    // A new exercise whose question sits under the header (Next pressed far down) glides up to it, as on the Quiz board.
    const header = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--app-header-h')) || 0
    if (body.current?.getBoundingClientRect().top < header) scrollToEl(body.current, 'top')
    body.current?.querySelector('input:not([readonly]), button:not([disabled])')?.focus({ preventScroll: true })
  }, [at])
  const status = (id) => (!(id in results) ? '' : results[id].correct ? 'right' : 'wrong')

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      <div className="flex gap-3 overflow-x-auto px-5 py-4 border-b border-[var(--border)] bg-[var(--surface-hi)]" role="group" aria-label="Exercises">
        {exercises.map((e, n) => (
          <AnswerSquare
            key={e.id}
            status={status(e.id)}
            number={n + 1}
            current={n === at}
            label={`Exercise ${n + 1}: ${status(e.id) || 'not done'}`}
            onClick={() => setAt(n)}
          />
        ))}
      </div>
      <div ref={body} className="p-5 space-y-5 scroll-mt-[calc(var(--app-header-h,0px)+1rem)]">
        <ExerciseHost
          key={current.id}
          exercise={current}
          accent={ACCENT}
          saved={results[current.id]}
          onDone={(correct, value) => setResults((prev) => ({ ...prev, [current.id]: { correct, value } }))}
        />
        <div className="flex items-center justify-between gap-4">
          <span className="type-small text-[var(--text-dim)]">
            {finished ? `${right} of ${exercises.length} right` : `${Object.keys(results).length} of ${exercises.length} done`}
          </span>
          {answered && at < exercises.length - 1 && <SmallButton ref={nextButton} onClick={() => { moved.current = true; setAt(at + 1) }}>Next exercise →</SmallButton>}
        </div>
      </div>
    </div>
  )
}
