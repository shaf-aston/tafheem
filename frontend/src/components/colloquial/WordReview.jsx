// Spaced review: the topic's words that are about to be forgotten, then the ones
// never tried, quizzed on the Quiz tab's own board. What is due comes from the
// app's one review schedule (lib/progress), which every word answer feeds.
import { useQuery } from '@tanstack/react-query'
import { useRef, useState } from 'react'

import { fetchSummary, recordAttempt } from '../../lib/progress'
import { QUIZ } from '../../lib/quizBanks'
import { fillIn, sayIn } from '../../lib/say'
import { useQuizRound } from '../../lib/useQuizRound'
import { useRememberedFlag } from '../../lib/useRemembered'
import { WORDS_MODULE } from '../../lib/wordDrills'
import { reviewOf, reviewQuestions } from '../../lib/wordReview'
import QuizBoard from '../QuizBoard'
import SmallButton from '../ui/SmallButton'

const dayOf = (iso) => new Date(iso).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'short' })
const say = sayIn('en')
const fill = fillIn('en')
const CARD = 'rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-6 text-center space-y-1'

// Frozen when it opens, so an answer saved mid-round does not reshuffle the round.
function Round({ words, rows, dialect, offline, onRestart }) {
  const [plan] = useState(() => reviewOf(words, rows, dialect))
  const [questions] = useState(() => reviewQuestions(plan.session, words, dialect))
  const [at, setAt] = useState(0)
  // The same switch as the Quiz tab's, so one setting governs both.
  const [autoNext, setAutoNext] = useRememberedFlag('quiz-auto-next', QUIZ.autoNext)
  // The last answer's save, waited for before planning again, so a word just answered is not asked as due.
  const saving = useRef(Promise.resolve())
  const round = useQuizRound({
    question: questions[at] ?? null,
    onAnswer: ({ question, correct, ms }) => { saving.current = recordAttempt({ module: WORDS_MODULE, item: question.answerId, correct, ms }) },
    onNext: () => setAt((n) => n + 1),
    autoNext,
    setAutoNext,
  })

  if (!questions.length) {
    return (
      <div className={CARD}>
        <p className="type-ui font-semibold text-[var(--text)]">All caught up</p>
        <p className="type-small text-[var(--text-dim)]">
          {plan.next ? `The next word comes back ${dayOf(plan.next)}.` : 'Every word here is learnt for now.'}
        </p>
      </div>
    )
  }

  const { history } = round
  const again = () => saving.current.then(onRestart)
  const total = history.length
  const right = history.filter((h) => h.correct).length

  return (
    <div className="space-y-3">
      <p className="type-small text-[var(--text-dim)]">
        {plan.later} of {words.length} learnt
        {plan.due > 0 && ` · ${plan.due} to remember again`}
        {plan.fresh > 0 && ` · ${plan.fresh} new`}
      </p>
      {offline && <p className="type-small text-[var(--warn)]">Your progress can't be reached, so every word is asked as new and answers may not be saved.</p>}
      <QuizBoard
        round={round}
        accent="var(--primary)"
        say={say}
        fill={fill}
        autoNext={autoNext}
        setAutoNext={setAutoNext}
        score={{ right, total }}
        bestStreak={0}
        onRestart={again}
      >
        <div className={`${CARD} flex flex-col items-center justify-center`}>
          <p className="type-ui font-semibold text-[var(--text)]">Round done</p>
          <p className="type-small text-[var(--text-dim)]">{right} of {total} right.</p>
          <SmallButton onClick={again}>Go again</SmallButton>
        </div>
      </QuizBoard>
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
  return <Round words={words} rows={summary.data ?? []} dialect={dialect} offline={summary.isError} onRestart={() => summary.refetch()} />
}
