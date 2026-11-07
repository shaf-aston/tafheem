/**
 * A lesson, one card at a time: pick, Check, Continue. Check marks the pick, then a panel rises at the foot with the
 * verdict and one line, holding Continue. The lesson holds focus mode (lib/shell/focus.js) until its end screen. Wrong
 * cards return once at the end; no hearts.
 * Cards are the exercise registry's; answers save like the Quiz's. Three right in a row shows a run; the end screen
 * sums the XP the server reported, how many were right first time, and how long the lesson took, recaps what was missed,
 * and offers the next lesson (`next`: its title and `go`) when there is one. Enter presses the footer's button (Check or
 * Continue), also from an answer option, and takes the focus once an answer is checked; leaving mid-lesson asks first
 * (focus in the question, Escape to stay), since it starts over. `onLeave` is the way on from the end screen; `onQuit`,
 * when given, is where the × goes instead (the Quiz rests there rather than dealing the next lesson). `guest`: nobody is
 * logged in, so the end screen says the XP is this device's until they log in.
 */
import { useEffect, useRef, useState } from 'react'

import { requeue } from '../../lib/grow/lesson'
import { useRecord } from '../../lib/learner/record'
import { rankOf, shareOf } from '../../lib/learner/rewards'
import { useFocusMode } from '../../lib/shell/focus'
import { sayIn } from '../../lib/text/say'
import ArabicText from '../ui/text/ArabicText'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import { kindOf } from './exercises'
import Medal from './Celebration'

const say = sayIn('en')

export default function LessonRunner({ cards: first, accent, rewards, guest = false, next: after, onLeave, onQuit = onLeave }) {
  const { file } = useRecord()
  const [cards, setCards] = useState(first)
  const [at, setAt] = useState(0)
  const [value, setValue] = useState(null)
  const [result, setResult] = useState(null)
  // `run`: answers right in a row, this lesson.
  const [tally, setTally] = useState({ asked: 0, right: 0, earned: 0, run: 0 })
  const [took, setTook] = useState(0)
  // The questions missed first time, for the end screen's recap.
  const [missed, setMissed] = useState([])
  // How each card went, by its place in the lesson: 'right', 'wrong' or 'seen'
  // (a card that teaches). The progress bar is drawn from it, so it is also the
  // lesson's record, and the end screen draws it again.
  const [marks, setMarks] = useState([])
  // When the current card appeared, for answer timing, and when the lesson began.
  const started = useRef(0)
  const begun = useRef(0)
  useEffect(() => { started.current = performance.now() }, [at])
  useEffect(() => { begun.current = performance.now() }, [])
  // The footer's button, for Enter and for focus after Check; `leaving` while "Leave this lesson?" is asked.
  const go = useRef(null)
  const [leaving, setLeaving] = useState(false)
  useEffect(() => { if (result) go.current?.focus() }, [result])
  // Enter on an answer option checks once the answer is ready (Space still picks); other controls keep their own Enter.
  useEffect(() => {
    if (leaving) return undefined
    const press = (event) => {
      if (event.key !== 'Enter') return
      const option = event.target.closest?.('.grow-option')
      if (option ? go.current?.disabled : event.target.closest?.('button, input, textarea, select, a')) return
      event.preventDefault()
      go.current?.click()
    }
    document.addEventListener('keydown', press)
    return () => document.removeEventListener('keydown', press)
  }, [leaving])
  // "Leave this lesson?" takes the focus on "Keep going", Escape keeps going, and the focus goes back to the ×.
  const stay = useRef(null)
  const x = useRef(null)
  useEffect(() => {
    if (!leaving) return undefined
    stay.current?.focus()
    const press = (event) => {
      if (event.key !== 'Escape') return
      setLeaving(false)
      x.current?.focus()
    }
    document.addEventListener('keydown', press)
    return () => document.removeEventListener('keydown', press)
  }, [leaving])
  function keepGoing() {
    setLeaving(false)
    x.current?.focus()
  }

  const done = at >= cards.length
  // While it runs the lesson has the screen: its × and bar are the only chrome. The end screen gives the app back.
  useFocusMode(!done)
  if (done) return <LessonDone tally={tally} took={took} missed={missed} marks={marks} accent={accent} rewards={rewards} guest={guest} next={after} onLeave={onLeave} />

  const card = cards[at]
  const kind = kindOf(card)
  const asks = Boolean(kind.check)

  function check(event) {
    const right = kind.check(card, value)
    setResult(right ? 'right' : 'wrong')
    setMarks((was) => Object.assign([...was], { [at]: right ? 'right' : 'wrong' }))
    // Only first showings count towards the score.
    setTally((was) => ({
      ...was,
      run: right ? was.run + 1 : 0,
      ...(!card.again && { asked: was.asked + 1, right: was.right + (right ? 1 : 0) }),
    }))
    if (!right) setCards(requeue(cards, at))
    if (!right && !card.again && card.ask) setMissed((was) => [...was, { id: card.id, ask: card.ask, ar: lineOf(card), why: card.why && kind.correction(card, value) }])
    const ms = Math.max(0, Math.round(event.timeStamp - started.current))
    file({ ...card.record, correct: right, ms }).then(({ earned = 0 }) => {
      if (earned) setTally((was) => ({ ...was, earned: was.earned + earned }))
    })
  }

  function next(event) {
    if (!asks) setMarks((was) => Object.assign([...was], { [at]: 'seen' }))
    if (at + 1 >= cards.length) setTook(event.timeStamp - begun.current)
    setAt(at + 1)
    setValue(null)
    setResult(null)
  }

  const said = result === 'right'
    ? kind.because?.(card)
    // A card comes back once: its second miss says only the answer.
    : result && [kind.correction(card, value), !card.again && say('It comes back at the end.')].filter(Boolean).join(' ')
  const { Card } = kind
  return (
    <div className="grow-lesson" style={{ '--w': accent }}>
      <div className="grow-lesson-top">
        <button ref={x} type="button" className="grow-x" aria-label={say('Leave the lesson')} onClick={() => (tally.asked ? setLeaving(true) : onQuit())}>
          <span aria-hidden="true">×</span>
        </button>
        <Segments count={cards.length} marks={marks} at={at} />
        {tally.run >= 3 && <span key={tally.run} className="grow-run pop">{say('{n} in a row', { n: tally.run })}</span>}
      </div>

      {leaving && (
        <div className="grow-leave" role="alertdialog" aria-modal="true" aria-labelledby="grow-leave-h">
          <p id="grow-leave-h">{say('Leave this lesson? Your answers are saved, but it starts again from the first card.')}</p>
          <button type="button" onClick={onQuit}>{say('Leave')}</button>
          <button ref={stay} type="button" className="grow-leave-stay" onClick={keepGoing}>{say('Keep going')}</button>
        </div>
      )}

      <div className="grow-lesson-card" inert={leaving}>
        <Card key={card.id} card={card} value={value} setValue={setValue} result={result} />
      </div>

      <div className="grow-lesson-foot" data-result={result ?? undefined} inert={leaving}>
        {/* The verdict, then one line: why, or the right answer. */}
        {result && (
          <p role="status" className="grow-lesson-say">
            <b>{say(result === 'right' ? 'Correct' : 'Not quite')}</b>
            {said && <> <span>{said}</span></>}
          </p>
        )}
        {asks && !result
          ? <PrimaryButton ref={go} accent={accent} disabled={!kind.ready(value, card)} onClick={check}>{say('Check')}</PrimaryButton>
          // After a check the button takes the verdict's colour, so the whole panel says right or wrong.
          : <PrimaryButton ref={go} accent={result ? `var(--${result === 'right' ? 'success' : 'danger'})` : accent} onClick={next}>{say('Continue')}</PrimaryButton>}
      </div>
    </div>
  )
}

/**
 * The lesson's progress as one segment per card, each filled as it goes: green
 * when right, rose when wrong, the accent once taught. A card missed and asked
 * again is a segment of its own, so the bar is the lesson's record too.
 */
function Segments({ count, marks, at = count }) {
  return (
    <span className="grow-segments" role="progressbar" aria-valuemin={0} aria-valuemax={count} aria-valuenow={Math.min(at, count)}
      aria-label={say('Lesson progress')} style={{ '--n': count }}>
      {Array.from({ length: count }, (_, i) => <i key={i} data-mark={marks[i]} data-here={i === at ? '' : undefined} />)}
    </span>
  )
}

/** A card's line of the book for the recap, its gap filled with the right word; none for a card without one. */
const lineOf = (card) => card.ar?.replace('____', card.options?.find((option) => option.id === card.answer)?.text ?? '____')

/** m:ss for a lesson's length. */
const clock = (ms) => {
  const seconds = Math.max(0, Math.round(ms / 1000))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

/** The medal and its burst, XP earned, right first time, the time taken, level progress, what was missed, what's next. */
function LessonDone({ tally, took, missed, marks, accent, rewards, guest, next, onLeave }) {
  const { asked, right, earned } = tally
  return (
    <div className="grow-lesson grow-lesson-done" style={{ '--w': accent }}>
      <Medal />
      <p className="grow-done-title">{say('Lesson done')}</p>
      <Segments count={marks.length} marks={marks} />
      <dl className="grow-done-stats">
        {/* No reading of XP (offline), no "+0". */}
        {rewards && <div><dt>{say('XP')}</dt><dd className="tabular-nums">+{earned}</dd></div>}
        <div><dt>{say('Right first time')}</dt><dd className="tabular-nums">{right}/{asked}</dd></div>
        <div><dt>{say('Time')}</dt><dd className="tabular-nums">{clock(took)}</dd></div>
      </dl>
      {rewards && (
        <div className="grow-done-level">
          <span>{say('Level {level}', { level: rewards.level })} · {rankOf(rewards.level).en}</span>
          <span className="tabular-nums">{rewards.into} / {rewards.need}</span>
          <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * shareOf(rewards)}%` }} /></span>
        </div>
      )}
      {guest && <p className="grow-hint">{say('Log in to keep your XP and streak on any device.')}</p>}
      {missed.length > 0 && (
        <section className="grow-done-missed" aria-labelledby="grow-missed-h">
          <h4 id="grow-missed-h">{say('What you missed')}</h4>
          <ul>
            {missed.slice(0, 3).map((one) => (
              <li key={one.id}><b>{one.ask}</b>{one.ar && <ArabicText as="p" size="sm" dir="rtl">{one.ar}</ArabicText>} {one.why}</li>
            ))}
          </ul>
        </section>
      )}
      {next ? (
        <div className="grow-done-go">
          <PrimaryButton accent={accent} onClick={next.go}>{say('Next: {title}', { title: next.title })}</PrimaryButton>
          <button type="button" className="grow-done-back" onClick={onLeave}>{say('Back to the path')}</button>
        </div>
      ) : <PrimaryButton accent={accent} onClick={onLeave}>{say('Continue')}</PrimaryButton>}
    </div>
  )
}
