/**
 * A lesson, one card at a time: pick, Check, Continue. Wrong cards return once at the end; no hearts.
 * Cards are the exercise registry's; answers save like the Quiz's, and the end screen sums the XP the server reported.
 */
import { useEffect, useRef, useState } from 'react'

import { requeue } from '../../lib/lesson'
import { recordAttempt } from '../../lib/progress'
import { rankOf, shareOf } from '../../lib/rewards'
import { sayIn } from '../../lib/say'
import PrimaryButton from '../ui/PrimaryButton'
import { kindOf } from './exercises'

const say = sayIn('en')

export default function LessonRunner({ cards: first, accent, rewards, onLeave }) {
  const [cards, setCards] = useState(first)
  const [at, setAt] = useState(0)
  const [value, setValue] = useState(null)
  const [result, setResult] = useState(null)
  const [tally, setTally] = useState({ asked: 0, right: 0, earned: 0 })
  // When the current card appeared, for answer timing.
  const started = useRef(0)
  useEffect(() => { started.current = performance.now() }, [at])

  const done = at >= cards.length
  if (done) return <LessonDone tally={tally} accent={accent} rewards={rewards} onLeave={onLeave} />

  const card = cards[at]
  const kind = kindOf(card)
  const asks = Boolean(kind.check)

  function check(event) {
    const right = kind.check(card, value)
    setResult(right ? 'right' : 'wrong')
    // Only first showings count towards the score.
    if (!card.again) setTally((was) => ({ ...was, asked: was.asked + 1, right: was.right + (right ? 1 : 0) }))
    if (!right) setCards(requeue(cards, at))
    const ms = Math.max(0, Math.round(event.timeStamp - started.current))
    recordAttempt({ ...card.record, correct: right, ms }).then(({ earned = 0 }) => {
      if (earned) setTally((was) => ({ ...was, earned: was.earned + earned }))
    })
  }

  function next() {
    setAt(at + 1)
    setValue(null)
    setResult(null)
  }

  const { Card } = kind
  return (
    <div className="grow-lesson" style={{ '--w': accent }}>
      <div className="grow-lesson-top">
        <button type="button" className="grow-x" aria-label={say('Leave the lesson')} onClick={onLeave}>
          <span aria-hidden="true">×</span>
        </button>
        <span className="grow-lesson-bar" role="progressbar" aria-valuemin={0} aria-valuemax={cards.length} aria-valuenow={at}
          aria-label={say('Lesson progress')}>
          <i style={{ width: `${(100 * at) / cards.length}%` }} />
        </span>
      </div>

      <Card key={card.id} card={card} value={value} setValue={setValue} result={result} />

      <div className="grow-lesson-foot" data-result={result ?? undefined}>
        {result && (
          <p role="status" className="grow-lesson-say">
            {result === 'right'
              ? [say('Right!'), kind.because?.(card)].filter(Boolean).join(' ')
              : `${kind.correction(card)} ${say('It comes back at the end.')}`}
          </p>
        )}
        {asks && !result
          ? <PrimaryButton accent={accent} disabled={!kind.ready(value, card)} onClick={check}>{say('Check')}</PrimaryButton>
          : <PrimaryButton accent={accent} onClick={next}>{say('Continue')}</PrimaryButton>}
      </div>
    </div>
  )
}

/** Score, XP earned, level progress. */
function LessonDone({ tally, accent, rewards, onLeave }) {
  const { asked, right, earned } = tally
  return (
    <div className="grow-lesson grow-lesson-done" style={{ '--w': accent }}>
      <p className="grow-done-title">{say('Lesson done')}</p>
      <p className="grow-done-score tabular-nums">{say('{right} of {asked} right first time', { right, asked })}</p>
      <dl className="grow-done-facts">
        <div><dt>{say('XP earned')}</dt><dd className="tabular-nums">+{earned}</dd></div>
        {rewards && (
          <div>
            <dt>{say('Level {level}', { level: rewards.level })} · {rankOf(rewards.level).en}</dt>
            <dd className="tabular-nums">{rewards.into} / {rewards.need}</dd>
          </div>
        )}
      </dl>
      {rewards && (
        <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * shareOf(rewards)}%` }} /></span>
      )}
      {!rewards && <p className="grow-hint">{say('Log in to keep your XP and streak on any device.')}</p>}
      <PrimaryButton accent={accent} onClick={onLeave}>{say('Continue')}</PrimaryButton>
    </div>
  )
}
